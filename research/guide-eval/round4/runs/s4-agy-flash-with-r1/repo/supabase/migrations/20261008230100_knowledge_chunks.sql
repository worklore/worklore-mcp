-- Knowledge base for drafts (eval/REPORT-v2.md) and triage results on items
-- (Yahhi/hearback#5). Was 20261015120000 (draft); applied as part of backend v1.
-- Change from the draft: every chunk carries a label. 'quotable' = her
-- published work (may be quoted and linked); 'background' = unpublished
-- material, context only, never quoted (REPORT-v2: private research leaked
-- into public drafts).
--
-- What drafts know beyond the thread is the founder's published body of work
-- (articles, stories, research, release notes, README, FAQ), cut into
-- ~300–600-token chunks, each with a date, a kind and, when public, a URL the
-- draft may cite. Retrieval per item: the top ~40 chunks by cosine published
-- BEFORE the item, then MMR + per-source cap in the engine (retrieve.ts).
--
-- Requires pgvector >= 0.8 (iterative index scans, so the project filter
-- doesn't starve the HNSW result).

create extension if not exists vector with schema extensions;
set search_path = public, extensions;

-- ------------------------------------------------------------------ documents
-- documents (init migration) holds whole sources; it gains what retrieval needs.
alter table documents
  add column published_at timestamptz,          -- when it became public (null = unknown → never retrieved)
  add column published_precision text not null default 'instant'
    check (published_precision in ('instant', 'day')),
  add column is_public boolean not null default true, -- false: a private source (e.g. a private repo); never linked in a draft
  add column source_ref text;                     -- where it came from when there's no public URL

-- ------------------------------------------------------------------ chunks
create table document_chunks (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  document_id uuid not null references documents(id) on delete cascade,
  ord int not null,                               -- position in the document
  kind text not null check (kind in ('article', 'story', 'research', 'changelog', 'readme', 'faq', 'fact')),
  title text not null,                            -- "Doc title › Section"
  source_url text,                                -- public link a draft may cite; null when not public
  source_ref text,
  -- A chunk is as new as its newest line (git blame for files): a README
  -- section written yesterday is not visible to a comment from last week.
  published_at timestamptz not null,
  published_precision text not null default 'instant' check (published_precision in ('instant', 'day')),
  content text not null,
  content_sha256 text not null,                   -- skip re-embedding unchanged chunks
  tokens int not null,
  lang text not null default 'en',
  embedding vector(768),                          -- gemini-embedding-001, outputDimensionality 768, L2-normalised
  embedding_model text,
  label text not null default 'quotable' check (label in ('quotable', 'background')),
  created_at timestamptz not null default now(),
  unique (document_id, ord)
);
create index document_chunks_project on document_chunks (project_id, published_at);
create index document_chunks_embedding on document_chunks
  using hnsw (embedding vector_cosine_ops) with (m = 16, ef_construction = 64);

alter table document_chunks enable row level security;
create policy members_all on document_chunks for all
  using (is_member(project_id)) with check (is_member(project_id));

-- ------------------------------------------------------------------ retrieval
-- Candidates for one item: published strictly before p_before (a day-precision
-- chunk only if its day is earlier: a same-day commit may be the answer to the
-- comment), optionally limited to kinds, nearest first. The engine re-ranks
-- (MMR, at most 2 per source) and keeps ~6. security invoker: RLS applies, so
-- a founder only ever retrieves her own projects' chunks.
create function match_document_chunks(
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
  select c.id, c.kind, c.title, c.source_url, c.source_ref,
         c.published_at, c.published_precision, c.content, c.tokens, c.lang,
         1 - (c.embedding <=> p_query) as similarity, c.embedding, c.label
  from document_chunks c
  where c.project_id = p_project
    and c.embedding is not null
    and (p_kinds is null or c.kind = any (p_kinds))
    and c.label = any (p_labels)
    and case c.published_precision
          when 'day' then (c.published_at at time zone 'utc')::date < (p_before at time zone 'utc')::date
          else c.published_at < p_before
        end
    and 1 - (c.embedding <=> p_query) >= p_min_similarity
  order by c.embedding <=> p_query
  limit greatest(1, least(p_count, 200));
$$;

-- ------------------------------------------------------------------ triage on items
-- triage.ts › TriageResult, as the app shows it: kind, route (decide_queue /
-- draft / short_draft / skip), not_sure, one-line summary, suggested action,
-- probabilities, and which decider answered (gemini / typesafe + model).
-- (generated columns for the app: see 20261008230200_backend_v1.sql)
alter table items
  add column triage jsonb,
  add column triage_route text generated always as (triage->>'route') stored;
create index items_triage_route on items (project_id, triage_route, posted_at desc);
