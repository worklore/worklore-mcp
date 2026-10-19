-- Backend v1 (docs/API.md): what the MVP screens need on top of the init
-- schema. Onboarding (project from a landing page), triage on items, drafts by
-- intent, ideas from feedback, the draft decision as one transaction, Vault
-- for Bluesky app passwords, an inbox view grouped by person, realtime.

-- ------------------------------------------------------------------ projects
alter table projects
  add column url text,
  add column description text,
  add column topics text[] not null default '{}',
  add column competitors text[] not null default '{}',
  add column aims text,
  add column landing jsonb,
  add column landing_read_at timestamptz,
  add column github_repo text check (github_repo is null or github_repo ~ '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'),
  add column knowledge_sources jsonb not null default '{}';
alter table projects alter column audience type text[]
  using case when audience is null or audience = '' then '{}'::text[] else array[audience] end;
alter table projects alter column audience set default '{}';
alter table projects alter column audience set not null;

-- ------------------------------------------------------------------ accounts
alter table accounts
  add column last_error text,
  add column settings jsonb not null default '{}';

-- The app may create a dev.to account row and switch accounts on/off, but
-- never set secret_id, external_id or the poll cursor: those belong to the
-- server (a forged secret_id could point the poller at another project's secret).
revoke insert, update on accounts from authenticated;
grant insert (project_id, platform, handle, auth, connected_by, active, settings) on accounts to authenticated;
grant update (project_id, platform, handle, auth, connected_by, active, settings) on accounts to authenticated;
alter table accounts add constraint accounts_app_no_secret check (auth <> 'none' or secret_id is null);

-- ------------------------------------------------------------------ people
alter table people add column stage_changed_at timestamptz;

create function people_touch_updated() returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  if new.stage is distinct from old.stage then new.stage_changed_at := now(); end if;
  return new;
end $$;
create trigger people_updated before update on people for each row execute function people_touch_updated();

-- ------------------------------------------------------------------ items
alter table items alter column account_id drop not null;
alter table items
  add column origin text not null default 'inbox' check (origin in ('inbox', 'discover')),
  add column triaged_at timestamptz,
  add column skip_reason text,
  add column discovery jsonb,
  add column triage_kind text generated always as (triage->>'kind') stored,
  add column triage_action text generated always as (triage->>'suggested_action') stored,
  add column triage_confidence real generated always as ((triage->>'confidence')::real) stored,
  add column triage_summary text generated always as (triage->>'summary') stored;
create index items_inbox on items (project_id, origin, status, posted_at desc);
create index items_untriaged on items (fetched_at) where triaged_at is null and origin = 'inbox';
create index items_person on items (person_id, posted_at desc);

-- ------------------------------------------------------------------ drafts
alter table drafts
  add column intent text check (intent in ('just_answer', 'invite_to_try', 'ask_feedback', 'ask_price', 'auto')),
  add column variant text not null default 'first' check (variant in ('first', 'shorter', 'redraft')),
  add column checks text[] not null default '{}',
  add column sources jsonb not null default '[]',
  add column lint jsonb,
  add column decided_by uuid references founders(id) on delete set null,
  add column decided_at timestamptz;

-- ------------------------------------------------------------------ ideas
-- Feedback turned into something to build. Similar asks from different
-- people are grouped into one idea; asked_by counts distinct people.
create table ideas (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  title text not null,
  summary text,
  quote text,                       -- the exact phrase heard (first ask)
  kind text not null default 'feature' check (kind in ('feature', 'bug', 'pain', 'would_pay', 'other')),
  asked_by int not null default 0,  -- distinct people, kept by trigger
  status text not null default 'new' check (status in ('new', 'planned', 'issue_open', 'not_now', 'done')),
  github_issue_url text,
  github_issue_number int,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index ideas_project on ideas (project_id, status, updated_at desc);

create table idea_items (
  idea_id uuid not null references ideas(id) on delete cascade,
  item_id uuid not null references items(id) on delete cascade,
  person_id uuid not null references people(id) on delete cascade,
  project_id uuid not null references projects(id) on delete cascade,
  quote text,
  created_at timestamptz not null default now(),
  primary key (idea_id, item_id)
);
create index idea_items_item on idea_items (item_id);

alter table ideas enable row level security;
create policy members_all on ideas for all using (is_member(project_id)) with check (is_member(project_id));
alter table idea_items enable row level security;
create policy members_all on idea_items for all using (is_member(project_id)) with check (is_member(project_id));

create function ideas_recount() returns trigger language plpgsql security definer set search_path = public as $$
declare i uuid := coalesce(new.idea_id, old.idea_id);
begin
  update ideas set asked_by = (select count(distinct person_id) from idea_items where idea_id = i), updated_at = now()
  where id = i;
  return null;
end $$;
create trigger idea_items_count after insert or delete on idea_items for each row execute function ideas_recount();

-- ------------------------------------------------------------------ decision RPC
-- The founder's decision on a draft, atomically (app/README.md asked for it).
-- security definer with an explicit membership check: the caller must be a
-- member of the draft's project.
create function record_draft_outcome(
  p_draft_id uuid,
  p_outcome draft_outcome,
  p_final_text text default null,
  p_posted_url text default null,
  p_move_stage person_stage default null
) returns drafts
language plpgsql security definer set search_path = public as $$
declare
  d drafts;
  it items;
  uid uuid := auth.uid();
  posted boolean := p_outcome in ('posted_as_is', 'posted_edited');
begin
  if p_outcome not in ('posted_as_is', 'posted_edited', 'skipped') then raise exception 'bad_outcome'; end if;
  if posted and coalesce(btrim(p_final_text), '') = '' then raise exception 'final_text_required'; end if;
  select * into d from drafts where id = p_draft_id for update;
  if not found then raise exception 'not_found'; end if;
  select * into it from items where id = d.item_id for update;
  if uid is null or not is_member(it.project_id) then raise exception 'not_found'; end if;
  if d.outcome is not null then raise exception 'already_decided'; end if;

  update drafts set
    outcome = p_outcome,
    final_text = case when posted then p_final_text else final_text end,
    posted_url = case when posted then p_posted_url else posted_url end,
    posted_at = case when posted then now() else posted_at end,
    posted_by = case when posted then uid else posted_by end,
    decided_by = uid, decided_at = now()
  where id = p_draft_id returning * into d;

  update drafts set outcome = 'superseded', decided_at = now()
  where item_id = it.id and id <> p_draft_id and outcome is null;

  update items set status = case when posted then 'answered'::item_status else 'skipped'::item_status end,
                   skip_reason = null
  where id = it.id;

  if posted then
    insert into touches (project_id, person_id, direction, platform, kind, occurred_at, url, text, item_id, by_founder, source)
    values (it.project_id, it.person_id, 'out', it.platform, 'reply', now(), p_posted_url, p_final_text, it.id, uid, 'app');
    update people set
      last_touch_at = now(),
      stage = coalesce(p_move_stage, case when stage = 'noticed' then 'talking'::person_stage else stage end)
    where id = it.person_id;
  elsif p_move_stage is not null then
    update people set stage = p_move_stage where id = it.person_id;
  end if;
  return d;
end $$;
revoke execute on function record_draft_outcome(uuid, draft_outcome, text, text, person_stage) from public, anon;
grant execute on function record_draft_outcome(uuid, draft_outcome, text, text, person_stage) to authenticated, service_role;

-- ------------------------------------------------------------------ Vault
-- Bluesky app passwords live in Vault; only the service role (Edge Functions)
-- can store or read them. The secret's name binds it to its account.
create function store_account_secret(p_account uuid, p_secret text) returns uuid
language plpgsql security definer set search_path = public, vault as $$
declare sid uuid;
begin
  select secret_id into sid from accounts where id = p_account;
  if not found then raise exception 'not_found'; end if;
  if sid is not null and exists (select 1 from vault.secrets where id = sid) then
    perform vault.update_secret(sid, p_secret);
  else
    sid := vault.create_secret(p_secret, 'account:' || p_account::text || ':' || gen_random_uuid()::text, 'hearback account credential');
    update accounts set secret_id = sid where id = p_account;
  end if;
  return sid;
end $$;

create function read_account_secret(p_account uuid) returns text
language sql stable security definer set search_path = public, vault as $$
  select s.decrypted_secret
  from accounts a join vault.decrypted_secrets s on s.id = a.secret_id
  where a.id = p_account and s.name like 'account:' || p_account::text || ':%';
$$;

create function delete_account_secret(p_account uuid) returns void
language plpgsql security definer set search_path = public, vault as $$
declare sid uuid;
begin
  select secret_id into sid from accounts where id = p_account;
  if sid is not null then
    delete from vault.secrets where id = sid;
    update accounts set secret_id = null where id = p_account;
  end if;
end $$;

revoke execute on function store_account_secret(uuid, text) from public, anon, authenticated;
revoke execute on function read_account_secret(uuid) from public, anon, authenticated;
revoke execute on function delete_account_secret(uuid) from public, anon, authenticated;
grant execute on function store_account_secret(uuid, text) to service_role;
grant execute on function read_account_secret(uuid) to service_role;
grant execute on function delete_account_secret(uuid) to service_role;

-- ------------------------------------------------------------------ inbox view
-- One row per person with something waiting (design 1g: grouped by person).
create view inbox_by_person with (security_invoker = true) as
with w as (
  select i.*, row_number() over (partition by i.person_id order by i.posted_at desc) rn
  from items i
  where i.origin = 'inbox' and i.status in ('new', 'draft_ready')
)
select
  w.project_id, w.person_id, p.display_name, p.avatar_url, p.stage,
  count(*)::int as waiting,
  count(*) filter (where w.status = 'new')::int as needs_you,
  count(*) filter (where w.status = 'draft_ready')::int as draft_ready,
  array_agg(distinct w.platform::text) as platforms,
  max(w.id::text) filter (where w.rn = 1)::uuid as last_item_id,
  max(w.text) filter (where w.rn = 1) as last_item_text,
  max(w.kind::text) filter (where w.rn = 1) as last_item_kind,
  max(w.platform::text) filter (where w.rn = 1) as last_item_platform,
  max(w.posted_at) as last_posted_at,
  max(w.status::text) filter (where w.rn = 1) as last_status,
  (select d.text from drafts d where d.item_id = max(w.id::text) filter (where w.rn = 1)::uuid and d.outcome is null
     order by d.version desc limit 1) as last_draft_text,
  exists (select 1 from idea_items ii where ii.person_id = w.person_id) as has_idea
from w join people p on p.id = w.person_id
group by w.project_id, w.person_id, p.display_name, p.avatar_url, p.stage;
revoke all on inbox_by_person from anon;
grant select on inbox_by_person to authenticated;

-- ------------------------------------------------------------------ realtime
do $$ begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    alter publication supabase_realtime add table items, drafts, ideas;
  end if;
end $$;

-- anon stays closed (20261008180000_no_anon) for everything created here.
revoke all on ideas, idea_items from anon;
