-- Ask the code (docs/ARCHITECTURE.md › Ask the code) and the model-call log.
--
-- model_calls: every model call the functions make (drafts, resolves,
-- points, triage summaries, decider, discover, landing reads, ask-code steps)
-- with tokens and list-price cost. Service role only; read it with SQL or
-- model_spend_daily. Drafts written before this log are copied in once
-- (purpose 'draft', fn 'backfill') from drafts.tokens.
--
-- code_questions: a question about the project's code (usually a draft's
-- [check: …] gap) and its answer with cited lines. answered_by 'cloud' is
-- the ask-code agent; 'local' is kept for a founder's own agent answering
-- from her machine (backlog). Members read their project's rows; only the
-- function writes them.

create table model_calls (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  fn text,                     -- the edge function (draft, triage, ask-code, …)
  purpose text not null,       -- draft / resolve / points / triage_summary / decide / discover_why / landing / ask_code
  project_id uuid references projects(id) on delete set null,
  founder_id uuid,             -- the signed-in founder (no FK: a log row must never fail to insert)
  item_id uuid references items(id) on delete set null,
  run_id uuid,                 -- the steps of one multi-step run (code_questions.id)
  provider text not null,
  model text not null,
  ok boolean not null,
  error text,
  tokens_in int,               -- all prompt tokens (uncached + cache reads + cache writes)
  tokens_out int,
  usage jsonb,                 -- {input, output, cache_read, cache_write, cost_usd}
  cost_usd numeric(12, 6),     -- list price (pricing.ts); null: unknown or free (Gemini free key)
  latency_ms int
);
create index model_calls_at on model_calls (at desc);
create index model_calls_project on model_calls (project_id, at desc);
create index model_calls_run on model_calls (run_id) where run_id is not null;
alter table model_calls enable row level security;  -- no policies: service role only
revoke all on model_calls from anon, authenticated;

insert into model_calls (at, fn, purpose, project_id, item_id, provider, model, ok, tokens_in, tokens_out, usage, cost_usd, latency_ms)
select d.created_at, 'backfill', 'draft', i.project_id, d.item_id, d.provider, d.model, true,
       d.tokens_in, d.tokens_out, d.tokens, nullif(d.tokens->>'cost_usd', '')::numeric, d.latency_ms
from drafts d join items i on i.id = d.item_id;

create view model_spend_daily with (security_invoker = true) as
select (at at time zone 'utc')::date as day, purpose, provider, model,
       count(*) as calls,
       count(*) filter (where not ok) as failed,
       sum(tokens_in) as tokens_in,
       sum(tokens_out) as tokens_out,
       round(sum(coalesce(cost_usd, 0)), 4) as cost_usd
from model_calls
group by 1, 2, 3, 4;
revoke all on model_spend_daily from anon, authenticated;

create table code_questions (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  item_id uuid references items(id) on delete set null,
  asked_by uuid references founders(id) on delete set null,
  question text not null check (length(question) between 3 and 2000),
  check_question text,         -- the [check: …] gap it answers, if any
  repo text not null,
  commit_sha text,             -- the code the answer was read at
  status text not null default 'running' check (status in ('running', 'answered', 'failed', 'waiting_local')),
  answered_by text not null default 'cloud' check (answered_by in ('cloud', 'local')),
  answer text,
  details text,
  sources jsonb not null default '[]',   -- [{path, start_line, end_line, note, url}]
  confidence text check (confidence in ('high', 'medium', 'low')),
  model text,
  steps int,
  usage jsonb,                 -- run totals: {input, output, cache_read, cache_write, cost_usd, tool_calls, github_requests}
  cost_usd numeric(12, 6),
  error text,
  created_at timestamptz not null default now(),
  answered_at timestamptz,
  used_at timestamptz          -- she used the answer (it was saved to the project's knowledge)
);
create index code_questions_item on code_questions (item_id, created_at desc);
create index code_questions_project on code_questions (project_id, created_at desc);
alter table code_questions enable row level security;
create policy members_read on code_questions for select using (is_member(project_id));
revoke insert, update, delete on code_questions from anon, authenticated;
