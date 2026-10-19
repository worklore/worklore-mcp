-- Server-side state for the collectors.
--  * Bluesky sessions: createSession is limited (30 per 5 min, 300 per day per
--    account), so the poller keeps the session (access + refresh JWT) in Vault
--    and refreshes it instead of logging in every 5 minutes.
--  * usage_counters: a per-day request cap for paid/free-tier model calls, so a
--    cron loop can't burn the day's quota.

create function store_account_session(p_account uuid, p_session text) returns void
language plpgsql security definer set search_path = public, vault as $$
declare sid uuid; nm text := 'account-session:' || p_account::text;
begin
  select id into sid from vault.secrets where name = nm;
  if sid is null then perform vault.create_secret(p_session, nm, 'hearback bluesky session');
  else perform vault.update_secret(sid, p_session); end if;
end $$;

create function read_account_session(p_account uuid) returns text
language sql stable security definer set search_path = public, vault as $$
  select decrypted_secret from vault.decrypted_secrets where name = 'account-session:' || p_account::text;
$$;

create or replace function delete_account_secret(p_account uuid) returns void
language plpgsql security definer set search_path = public, vault as $$
declare sid uuid;
begin
  select secret_id into sid from accounts where id = p_account;
  if sid is not null then
    delete from vault.secrets where id = sid;
    update accounts set secret_id = null where id = p_account;
  end if;
  delete from vault.secrets where name = 'account-session:' || p_account::text;
end $$;

revoke execute on function store_account_session(uuid, text) from public, anon, authenticated;
revoke execute on function read_account_session(uuid) from public, anon, authenticated;
grant execute on function store_account_session(uuid, text) to service_role;
grant execute on function read_account_session(uuid) to service_role;

create table usage_counters (
  day date not null default (now() at time zone 'utc')::date,
  key text not null,
  n int not null default 0,
  primary key (day, key)
);
alter table usage_counters enable row level security;  -- no policies: service role only
revoke all on usage_counters from anon, authenticated;

-- Adds one request under p_key for today; false (and no increment) when the cap is reached.
create function bump_usage(p_key text, p_cap int) returns boolean
language plpgsql security definer set search_path = public as $$
declare cur int;
begin
  insert into usage_counters (key, n) values (p_key, 0) on conflict do nothing;
  select n into cur from usage_counters where day = (now() at time zone 'utc')::date and key = p_key for update;
  if cur >= p_cap then return false; end if;
  update usage_counters set n = n + 1 where day = (now() at time zone 'utc')::date and key = p_key;
  return true;
end $$;
revoke execute on function bump_usage(text, int) from public, anon, authenticated;
grant execute on function bump_usage(text, int) to service_role;
