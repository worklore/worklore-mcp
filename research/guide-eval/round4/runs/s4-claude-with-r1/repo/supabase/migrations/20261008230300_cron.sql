-- Background polling: pg_cron calls the Edge Functions through pg_net with the
-- service role. The URL and key are read from Vault at run time (secrets
-- 'hb_project_url' and 'hb_service_role', set by scripts/set-cron-secrets.sh),
-- so nothing secret is in this file or in cron.job.
create extension if not exists pg_cron with schema pg_catalog;
create extension if not exists pg_net with schema extensions;

create or replace function hb_call_function(p_name text, p_body jsonb default '{}') returns bigint
language plpgsql security definer set search_path = public, extensions, vault as $$
declare
  base text := (select decrypted_secret from vault.decrypted_secrets where name = 'hb_project_url');
  key text := (select decrypted_secret from vault.decrypted_secrets where name = 'hb_service_role');
begin
  if base is null or key is null then
    raise warning 'hb_call_function: vault secrets hb_project_url / hb_service_role are missing';
    return null;
  end if;
  return net.http_post(
    url := base || '/functions/v1/' || p_name,
    headers := jsonb_build_object('content-type', 'application/json', 'authorization', 'Bearer ' || key),
    body := p_body,
    timeout_milliseconds := 150000);
end $$;
revoke execute on function hb_call_function(text, jsonb) from public, anon, authenticated;

select cron.schedule('hb-poll-bluesky', '*/5 * * * *', $$select hb_call_function('poll-bluesky')$$);
select cron.schedule('hb-poll-devto-public', '*/15 * * * *', $$select hb_call_function('poll-devto-public')$$);
-- Items that arrived but weren't triaged inline (caps, model errors).
select cron.schedule('hb-triage-pending', '2-59/5 * * * *', $$select hb_call_function('triage', '{"pending": true}')$$);
