-- Drafts by a configurable model (Claude or Gemini), 2026-10-09.
--
-- projects.settings: per-project switches the server reads; today only
--   draft_model  "anthropic:claude-sonnet-5-5" | "gemini:gemini-3.1-flash-lite" | …
--                (overrides the DRAFT_MODEL function secret for this project)
--   draft_effort "low" | "medium" | "high" (Claude only)
-- Written by the service role only (no grant to authenticated); members read it
-- with the rest of the project row.
--
-- drafts.tokens: the provider's usage breakdown for the draft:
--   {input, output, cache_read?, cache_write?, cost_usd?}
-- (tokens_in / tokens_out stay as the totals.)

alter table projects add column if not exists settings jsonb not null default '{}';
alter table drafts add column if not exists tokens jsonb;
