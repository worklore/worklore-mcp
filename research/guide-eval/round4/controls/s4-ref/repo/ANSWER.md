# Not in 3NF

1. model_calls: tokens_in, tokens_out and cost_usd are stored next to the usage jsonb that already holds input/output/cache_read/cache_write/cost_usd. The functions write both; nothing keeps them equal. Same pattern the 2026-10-10 migration fixed on drafts with generated columns.
2. code_questions: usage, cost_usd, steps and model are totals over the model_calls rows of the run (run_id = code_questions.id), kept by hand in ask-code; no trigger.
3. Kept on purpose and guarded: project_id copies on child tables (composite foreign keys since 2026-10-10), ideas.asked_by and people.first_touch_at/last_touch_at (triggers).
4. 1NF, debatable: ideas.result_links, code_questions.sources and drafts.meta.resolved are jsonb lists; fine while nothing queries inside them.

Already fixed by 20261010040000_normal_forms.sql: idea_items.person_id (dropped), document_chunks' kind/label/source_url (dropped), plans.allowed_models (now plan_models), drafts.tokens_in/out (generated).
