-- Normal forms, 2026-10-10. The schema checked against 1NF–3NF (Codd 1970/71),
-- BCNF and 4NF/5NF (Fagin 1977/79); in Kent's words (CACM 26(2), 1983), every
-- non-key field is a fact about the key, the whole key, and nothing but the key.
--
-- Mixed approach, not textbook 3NF:
--   * redundancy that buys nothing is removed, or computed by Postgres
--     (generated columns, triggers) so it can't drift;
--   * the project_id copies on child tables stay (RLS policies and the hot
--     indexes filter on them), but composite foreign keys now make a copy that
--     disagrees with its parent impossible.
-- Every constraint below was checked against the live data first (no
-- violations). Left as they are, on purpose:
--   * ideas.github_issue_url: holds either the issue's URL or a pre-filled
--     github.com "new issue" link (app), so it isn't derivable from repo + number;
--   * source_syncs.source ('devto:writing:<handle>', 'github:<repo>'): an
--     opaque key the app shows and parses; the database only compares it;
--   * voice_samples.text_sha256: the server dedupes on it before inserting,
--     with JavaScript's whitespace rule; a generated column could disagree;
--   * themes.position vs project_memory kind 'position': both unused so far.

set search_path = public, extensions;

-- ------------------------------------------------------------------ 3NF: project_id copies
-- Parents expose (id, project_id[, …]) so children can reference the pair.
alter table people   add constraint people_id_project unique (id, project_id);
alter table accounts add constraint accounts_id_project_platform unique (id, project_id, platform);
alter table items    add constraint items_id_project unique (id, project_id),
                     add constraint items_id_project_person unique (id, project_id, person_id);
alter table documents add constraint documents_id_project unique (id, project_id);
alter table ideas    add constraint ideas_id_project unique (id, project_id);
alter table themes   add constraint themes_id_project unique (id, project_id);

-- An item's person and account are in the item's project; the account is on
-- the item's platform. (Discover items have no account: MATCH SIMPLE skips it.)
alter table items
  drop constraint items_person_id_fkey,
  add constraint items_person_fkey foreign key (person_id, project_id) references people (id, project_id) on delete cascade,
  drop constraint items_account_id_fkey,
  add constraint items_account_fkey foreign key (account_id, project_id, platform)
    references accounts (id, project_id, platform) on delete cascade;

alter table identities
  drop constraint identities_person_id_fkey,
  add constraint identities_person_fkey foreign key (person_id, project_id) references people (id, project_id) on delete cascade;

-- A touch about an item is with that item's person; if the item moves to
-- another person (people merged), its touches follow.
alter table touches
  drop constraint touches_person_id_fkey,
  add constraint touches_person_fkey foreign key (person_id, project_id) references people (id, project_id) on delete cascade,
  drop constraint touches_item_id_fkey,
  add constraint touches_item_fkey foreign key (item_id, project_id, person_id)
    references items (id, project_id, person_id) on delete cascade on update cascade;

alter table document_chunks
  drop constraint document_chunks_document_id_fkey,
  add constraint document_chunks_document_fkey foreign key (document_id, project_id) references documents (id, project_id) on delete cascade;

alter table idea_items
  drop constraint idea_items_idea_id_fkey,
  add constraint idea_items_idea_fkey foreign key (idea_id, project_id) references ideas (id, project_id) on delete cascade,
  drop constraint idea_items_item_id_fkey,
  add constraint idea_items_item_fkey foreign key (item_id, project_id) references items (id, project_id) on delete cascade;

-- A theme from another project can't be attached.
alter table documents
  drop constraint documents_theme_id_fkey,
  add constraint documents_theme_fkey foreign key (theme_id, project_id) references themes (id, project_id) on delete set null (theme_id);
alter table project_memory
  drop constraint project_memory_theme_id_fkey,
  add constraint project_memory_theme_fkey foreign key (theme_id, project_id) references themes (id, project_id) on delete cascade;

-- ------------------------------------------------------------------ 2NF: idea_items.person_id
-- idea_items is keyed by (idea_id, item_id), but person_id depended on item_id
-- alone (it is items.person_id). Who asked is now read through the item.
create or replace function ideas_recount() returns trigger language plpgsql security definer set search_path = public as $$
declare x uuid := coalesce(new.idea_id, old.idea_id);
begin
  update ideas set asked_by = (
      select count(distinct i.person_id) from idea_items ii join items i on i.id = ii.item_id where ii.idea_id = x),
    updated_at = now()
  where id = x;
  return null;
end $$;

-- asked_by stays a cached count: recount when an item changes hands.
create function items_person_recount() returns trigger language plpgsql security definer set search_path = public as $$
begin
  update ideas d set asked_by = (
      select count(distinct i.person_id) from idea_items ii join items i on i.id = ii.item_id where ii.idea_id = d.id)
  where d.id in (select idea_id from idea_items where item_id = new.id);
  return null;
end $$;
create trigger items_person_recount after update of person_id on items
  for each row when (old.person_id is distinct from new.person_id) execute function items_person_recount();
revoke execute on function items_person_recount() from public, anon, authenticated;

-- The inbox view read idea_items.person_id; same columns, through items.
create or replace view inbox_by_person with (security_invoker = true) as
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
  exists (select 1 from idea_items ii join items ai on ai.id = ii.item_id where ai.person_id = w.person_id) as has_idea
from w join people p on p.id = w.person_id
group by w.project_id, w.person_id, p.display_name, p.avatar_url, p.stage;

alter table idea_items drop column person_id;

-- ------------------------------------------------------------------ 3NF: document_chunks
-- kind, source_url, source_ref and label were copies of the chunk's document
-- (written from it in knowledge.ts; identical on every live row). They live on
-- documents only. published_at / published_precision stay per chunk (a section
-- is as new as its newest line), and so does lang.
alter table documents add constraint documents_kind_check
  check (kind in ('article', 'story', 'research', 'changelog', 'readme', 'faq', 'fact', 'page'));

-- is_public was label = 'quotable' written twice; Postgres computes it now.
alter table documents drop column is_public;
alter table documents add column is_public boolean generated always as (label = 'quotable') stored;

-- Same signature and result as before; the document's fields come through the join.
create or replace function match_document_chunks(
  p_project uuid,
  p_query vector(768),
  p_before timestamptz default now(),
  p_count int default 40,
  p_kinds text[] default null,
  p_min_similarity float default 0.68,
  p_labels text[] default array['quotable']
) returns table (
  id uuid, kind text, title text, source_url text, source_ref text,
  published_at timestamptz, published_precision text, content text, tokens int, lang text,
  similarity float, embedding vector(768), label text
)
language sql stable security invoker
set search_path = public, extensions
set hnsw.ef_search = 100
set hnsw.iterative_scan = relaxed_order
as $$
  select c.id, d.kind, c.title,
         case when d.label = 'quotable' then d.url end as source_url,
         case when d.label <> 'quotable' then coalesce(d.source_ref, d.url) end as source_ref,
         c.published_at, c.published_precision, c.content, c.tokens, c.lang,
         1 - (c.embedding <=> p_query) as similarity, c.embedding, d.label
  from document_chunks c
  join documents d on d.id = c.document_id
  where c.project_id = p_project
    and c.embedding is not null
    and (p_kinds is null or d.kind = any (p_kinds))
    and d.label = any (p_labels)
    and case c.published_precision
          when 'day' then (c.published_at at time zone 'utc')::date < (p_before at time zone 'utc')::date
          else c.published_at < p_before
        end
    and 1 - (c.embedding <=> p_query) >= p_min_similarity
  order by c.embedding <=> p_query
  limit greatest(1, least(p_count, 200));
$$;

alter table document_chunks drop column kind, drop column source_url, drop column source_ref, drop column label;

-- ------------------------------------------------------------------ 3NF: drafts.tokens_in / tokens_out
-- The totals are functions of the usage breakdown in drafts.tokens (Anthropic's
-- input excludes cache reads and writes; the total includes them). Drafts that
-- only had totals (Gemini) get them as the breakdown, then Postgres computes
-- the totals.
update drafts set tokens = jsonb_build_object('input', tokens_in, 'output', tokens_out)
  where tokens is null and (tokens_in is not null or tokens_out is not null);

do $$ begin
  if exists (select 1 from drafts where
      tokens_in is distinct from (tokens->>'input')::int + coalesce((tokens->>'cache_read')::int, 0) + coalesce((tokens->>'cache_write')::int, 0)
      or tokens_out is distinct from (tokens->>'output')::int) then
    raise exception 'drafts: tokens_in/tokens_out disagree with drafts.tokens; not converting';
  end if;
end $$;

alter table drafts drop column tokens_in, drop column tokens_out;
alter table drafts
  add column tokens_in int generated always as
    ((tokens->>'input')::int + coalesce((tokens->>'cache_read')::int, 0) + coalesce((tokens->>'cache_write')::int, 0)) stored,
  add column tokens_out int generated always as ((tokens->>'output')::int) stored;

-- ------------------------------------------------------------------ derived: people.first/last_touch_at
-- Kept as a cache of min/max(touches.occurred_at), now by the database for
-- every writer (the collector did read-then-write; issue touches didn't update
-- it at all). greatest/least on insert is safe under concurrent inserts.
create function touches_person_span() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update people set first_touch_at = least(first_touch_at, new.occurred_at),
                      last_touch_at = greatest(last_touch_at, new.occurred_at)
    where id = new.person_id
      and (first_touch_at is null or last_touch_at is null or new.occurred_at < first_touch_at or new.occurred_at > last_touch_at);
  else
    update people p set first_touch_at = s.lo, last_touch_at = s.hi
    from (select x.id, (select min(occurred_at) from touches where person_id = x.id) lo,
                       (select max(occurred_at) from touches where person_id = x.id) hi
          from (select old.person_id as id union select new.person_id) x where x.id is not null) s
    where p.id = s.id;
  end if;
  return null;
end $$;
create trigger touches_person_span after insert or delete or update of person_id, occurred_at on touches
  for each row execute function touches_person_span();
revoke execute on function touches_person_span() from public, anon, authenticated;

-- The decision RPC no longer sets last_touch_at itself: its touch does.
create or replace function record_draft_outcome(
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
      stage = coalesce(p_move_stage, case when stage = 'noticed' then 'talking'::person_stage else stage end)
    where id = it.person_id;
  elsif p_move_stage is not null then
    update people set stage = p_move_stage where id = it.person_id;
  end if;
  return d;
end $$;

-- ------------------------------------------------------------------ 1NF: plans.allowed_models
-- The array was a relation in disguise (searched with = any in three
-- functions). One row per (plan, model); ord keeps the order the app lists.
create table plan_models (
  plan_id text not null,
  model text not null,
  ord smallint not null default 0,
  primary key (plan_id, model),
  constraint plan_models_plan_fkey foreign key (plan_id) references plans (id) on delete cascade
);
insert into plan_models (plan_id, model, ord)
  select p.id, m.model, m.n from plans p, unnest(p.allowed_models) with ordinality as m(model, n);

-- The default is one of the plan's models (deferred: a plan and its models are
-- inserted in one transaction).
alter table plans drop constraint plans_default_allowed;
alter table plans add constraint plans_default_model_fkey foreign key (id, default_model)
  references plan_models (plan_id, model) deferrable initially deferred;

alter table plan_models enable row level security;
create policy signed_in_read on plan_models for select to authenticated using (true);
revoke all on plan_models from anon, authenticated;
grant select on plan_models to authenticated;

-- Same rule as before: an override is checked when it is set; if the plan later
-- drops the model (or the founder changes plan), the server falls back to the
-- plan default instead. That's why this stays a trigger, not a foreign key.
create or replace function check_founder_draft_model() returns trigger
  language plpgsql set search_path = public as $$
begin
  if new.draft_model is not null
     and (tg_op = 'INSERT' or new.draft_model is distinct from old.draft_model)
     and not exists (select 1 from plan_models m where m.plan_id = new.plan_id and m.model = new.draft_model) then
    raise exception 'model_not_allowed' using errcode = '23514', detail = format('%s is not in plan %s', new.draft_model, new.plan_id);
  end if;
  return new;
end $$;

create or replace function my_draft_model() returns jsonb
  language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'plan_id', p.id, 'plan_name', p.name, 'default_model', p.default_model,
    'allowed_models', coalesce((select jsonb_agg(m.model order by m.ord, m.model) from plan_models m where m.plan_id = p.id), '[]'::jsonb),
    'draft_model', f.draft_model,
    'effective_model', case when exists (select 1 from plan_models m where m.plan_id = p.id and m.model = f.draft_model)
                            then f.draft_model else p.default_model end)
  from founders f join plans p on p.id = f.plan_id
  where f.id = auth.uid()
$$;

create or replace function set_draft_model(model text) returns jsonb
  language plpgsql security definer set search_path = public as $$
declare
  m text := nullif(btrim(model), '');
begin
  if auth.uid() is null then raise exception 'not_found'; end if;
  if m is not null and not exists (
    select 1 from founders f join plan_models pm on pm.plan_id = f.plan_id
    where f.id = auth.uid() and pm.model = m) then
    raise exception 'model_not_allowed' using errcode = '23514';
  end if;
  update founders set draft_model = m where id = auth.uid();
  if not found then raise exception 'not_found'; end if;
  return my_draft_model();
end $$;

alter table plans drop column allowed_models;
