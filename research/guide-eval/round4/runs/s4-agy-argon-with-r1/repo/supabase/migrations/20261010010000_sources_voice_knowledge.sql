-- Sources: voice samples and the knowledge base, built by one reproducible
-- pipeline for every founder (docs/ARCHITECTURE.md › Sources: voice and
-- knowledge). Nothing per-user is hand-made: connectors bring the founder's
-- own writing (ownWriting) and published work (publishedWork), GitHub brings
-- the project's `hearback/` folder, the landing page brings the site; the core
-- stores, judges (TypeSafe Jev) and selects.

-- ------------------------------------------------------------------ voice samples
-- Voice is personal: rows belong to a founder, not to a project. project_id
-- only says where the sample was found.
create table voice_samples (
  id uuid primary key default gen_random_uuid(),
  founder_id uuid not null references founders(id) on delete cascade,
  project_id uuid references projects(id) on delete set null,
  platform text not null,                 -- connector id (devto, github, …) or the platform a Hearback reply went to
  source text not null check (source in ('own_writing', 'hearback', 'github')),
  external_id text not null,              -- platform id: dev.to id_code, 'draft:<uuid>', '<repo>:<path>#<n>'
  source_url text,
  text text not null,
  context text,                           -- what it answered (or the article / file it sits in)
  posted_at timestamptz,                  -- when she wrote it (real date; evals exclude samples written after an item)
  text_sha256 text not null,              -- of the whitespace-normalised text: dedupe across sources
  status text not null default 'candidate' check (status in ('candidate', 'accepted', 'rejected')),
  reason text,                            -- why rejected / accepted ('rule: emoji_only', 'decider: …')
  scores jsonb,                           -- decider answers {meaningful, quality, decider, model}
  quality real,                           -- 0–4 (decider's expected level)
  active boolean not null default false,  -- in the capped set drafts draw from
  decided_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (founder_id, platform, external_id),
  unique (founder_id, text_sha256)
);
create index voice_samples_pending on voice_samples (created_at) where status = 'candidate';
create index voice_samples_active on voice_samples (founder_id) where active;

alter table voice_samples enable row level security;
-- Only the founder herself reads her samples; the server writes them.
create policy self_read on voice_samples for select using (founder_id = auth.uid());
revoke insert, update, delete on voice_samples from anon, authenticated;

-- ------------------------------------------------------------------ sync state
-- One row per project and source: ETags, file SHAs, per-article counts, and
-- what the app shows (status, message, last sync).
create table source_syncs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  source text not null,                   -- 'devto:writing:yahhi', 'devto:articles:yahhi', 'github:owner/repo', 'landing'
  state jsonb not null default '{}',
  status text not null default 'ok' check (status in ('ok', 'error', 'needs_auth', 'rate_limited', 'empty')),
  message text,
  stats jsonb,
  last_synced_at timestamptz,
  unique (project_id, source)
);
alter table source_syncs enable row level security;
create policy members_read on source_syncs for select using (is_member(project_id));
revoke insert, update, delete on source_syncs from anon, authenticated;

-- ------------------------------------------------------------------ knowledge
-- Which pipeline source produced a document, and a hash of it so a re-run
-- skips unchanged documents. 'seed' = written by the one-off seed script and
-- not (yet) reproduced by the pipeline; kept, still retrieved.
alter table documents
  add column source text,
  add column content_sha256 text,
  add column label text not null default 'quotable' check (label in ('quotable', 'background'));
create index documents_source on documents (project_id, source);

-- Pages of the product's own site (landing + linked pages).
alter table document_chunks drop constraint document_chunks_kind_check;
alter table document_chunks add constraint document_chunks_kind_check
  check (kind in ('article', 'story', 'research', 'changelog', 'readme', 'faq', 'fact', 'page'));

-- The folder in the linked GitHub repo whose .md/.txt files are synced.
alter table projects add column github_folder text not null default 'hearback'
  check (github_folder ~ '^[A-Za-z0-9_. -]+(/[A-Za-z0-9_. -]+)*$' and github_folder !~ '(^|/)\.\.(/|$)');

-- ------------------------------------------------------------------ posted replies
-- A reply she posted through Hearback is the best voice sample: it becomes a
-- candidate at once; the judge cron decides within minutes.
create or replace function hb_voice_from_draft() returns trigger
language plpgsql security definer set search_path = public, extensions as $$
declare
  it record;
  norm text;
begin
  if new.outcome not in ('posted_as_is', 'posted_edited') or coalesce(trim(new.final_text), '') = '' then return new; end if;
  if old.outcome is not distinct from new.outcome then return new; end if;
  select i.project_id, i.platform::text as platform, left(i.text, 600) as text into it from items i where i.id = new.item_id;
  norm := regexp_replace(trim(new.final_text), '\s+', ' ', 'g');
  insert into voice_samples (founder_id, project_id, platform, source, external_id, source_url, text, context, posted_at, text_sha256)
  values (coalesce(new.posted_by, new.decided_by), it.project_id, it.platform, 'hearback', 'draft:' || new.id, new.posted_url,
          new.final_text, it.text, coalesce(new.posted_at, now()), encode(digest(norm, 'sha256'), 'hex'))
  on conflict do nothing;
  return new;
exception when others then
  raise warning 'hb_voice_from_draft: %', sqlerrm;
  return new;
end $$;

create trigger drafts_voice_sample after update of outcome on drafts
  for each row when (new.outcome in ('posted_as_is', 'posted_edited'))
  execute function hb_voice_from_draft();

-- ------------------------------------------------------------------ app summary
-- What the Project tab shows: the signed-in founder's voice samples, the
-- project's documents by source, and the last sync per source.
create or replace function source_summary(p_project uuid) returns jsonb
language sql stable security invoker set search_path = public as $$
  select jsonb_build_object(
    'voice', (select jsonb_build_object(
        'accepted', count(*) filter (where status = 'accepted'),
        'active', count(*) filter (where active),
        'candidates', count(*) filter (where status = 'candidate'),
        'rejected', count(*) filter (where status = 'rejected'))
      from voice_samples where founder_id = auth.uid()),
    'knowledge', (select coalesce(jsonb_object_agg(src, n), '{}'::jsonb)
      from (select coalesce(source, 'other') as src, count(*) as n from documents where project_id = p_project group by 1) s),
    'syncs', (select coalesce(jsonb_agg(jsonb_build_object('source', source, 'status', status, 'message', message,
        'last_synced_at', last_synced_at, 'stats', stats) order by source), '[]'::jsonb)
      from source_syncs where project_id = p_project),
    'last_synced_at', (select max(last_synced_at) from source_syncs where project_id = p_project),
    'github', (select jsonb_build_object('repo', github_repo, 'folder', github_folder) from projects where id = p_project)
  )
$$;
revoke execute on function source_summary(uuid) from public, anon;
grant execute on function source_summary(uuid) to authenticated;

-- ------------------------------------------------------------------ schedule
-- Daily: every project's sources (own writing, articles, GitHub folder, site).
select cron.schedule('hb-sources-daily', '17 4 * * *', $$select hb_call_function('sources-sync', '{}')$$);
-- Every 10 min: judge new candidates (e.g. a reply she just posted) and embed new chunks. A no-op when idle.
select cron.schedule('hb-sources-judge', '7-59/10 * * * *', $$select hb_call_function('sources-sync', '{"phase": "judge"}')$$);
