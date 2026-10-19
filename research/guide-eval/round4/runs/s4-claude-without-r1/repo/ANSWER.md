# Where the schema isn't in 3NF

This covers the schema as it stands after every migration in `supabase/migrations/` has run (so `idea_items.person_id`, the copied `document_chunks` columns and `plans.allowed_models` are already gone). I checked each table on its own, which is how 3NF is defined: a non-key column must depend on a key, the whole key, and nothing else. The one exception is a column that is itself part of some candidate key (a "prime" column).

The findings fall into three groups:

- **A. Not in 3NF, and nothing stops the copies from disagreeing.** These are the ones to act on.
- **B. Not in 3NF on paper, but Postgres keeps them consistent** (generated columns or composite foreign keys). This was a deliberate choice in `20261010040000_normal_forms.sql`.
- **C. Look like violations but aren't** (or aren't 3NF questions).

---

## A. Not in 3NF, not enforced

| # | Table.column(s) | Dependency that breaks 3NF | How it drifts today |
|---|---|---|---|
| 1 | `model_calls.tokens_in`, `tokens_out`, `cost_usd` | `id → usage → tokens_in / tokens_out / cost_usd`. All three are functions of the `usage` JSON in the same row. | Each caller works them out separately: `ask_code.ts:90` adds `input + cache_read + cache_write` itself, and `models.ts:47` passes on whatever the provider returned. `drafts` had this exact problem and fixed it with generated columns (`20261010040000`, `20261011120000`). `model_calls` brought it back. |
| 2 | `model_calls.project_id` | `item_id → project_id` (the item's project). | Both are plain single-column FKs with no composite FK, so a row can name an item from one project and a different `project_id`. |
| 3 | `code_questions.cost_usd` | `id → usage → cost_usd` (it is `usage->>'cost_usd'`). It's also the sum of `model_calls.cost_usd` for `run_id = id`. | They already disagree. On success both come from `run.usage` (`ask_code.ts:97`). On failure, `cost_usd` is set from the `model_calls` sum and `usage` stays null (`ask_code.ts:104-106`). |
| 4 | `code_questions.project_id` | `item_id → project_id`. | Plain FKs, same as #2. |
| 5 | `voice_samples.quality` | `id → scores → quality`. `voice.ts:96-100` writes the same number into `quality` and `scores.quality`. | Two writable copies of one value. |
| 6 | `documents.content_sha256`, `document_chunks.content_sha256` (and `document_chunks.tokens`) | `content → content_sha256` (and `content → tokens` for a fixed tokenizer). The hash isn't part of any key: the keys are `(project_id, url)` and `(document_id, ord)`. | The server writes them. Editing `content` any other way leaves a stale hash, and "skip unchanged" then skips a document that did change. |
| 7 | `drafts.provider`, `model_calls.provider` | `model → provider`, a non-key column determining another non-key column. `providers/index.ts:39-40` derives the provider from the model name (`claude-*` → anthropic). | Nothing stops a row like `('gemini', 'claude-opus-5-5')`. |
| 8 | `projects.github_board_title` (and `github_board_id`) | `(github_board_owner, github_board_number) → github_board_id → github_board_title`. Owner and number are the board's address; the id and title are facts about that board, cached from GitHub. | The `projects_github_board_whole` check only makes the columns null together. Nothing refreshes the title, and nothing ties the id to the address. |
| 9 | `items.my_post` | `item → the post it's under → my_post {url, title, text}`. The snapshot is a fact about the founder's post, repeated on every item under that post. | `store.ts:108-113` (`richerContext`) updates it one item at a time, so comments under the same article can hold different titles or texts for it. |
| 10 | `touches.platform` (for touches with an `item_id`) | `item_id → platform`. | The composite FK `touches_item_fkey` covers `(item_id, project_id, person_id)` but not `platform`, so a touch can name a different platform than its item. |

Smaller items of the same kind:

- **`drafts.posted_at` and `posted_by` vs `decided_at` and `decided_by`.** When `outcome` is `posted_*`, `record_draft_outcome` sets each pair from the same `now()` and the same `uid`, so the posted pair repeats the decided pair. Strictly this is a conditional dependency, not a plain one.
- **`ideas.github_issue_url` vs `(github_issue_repo, github_issue_number)`, and `ideas.github_issue_state` vs `github_issue_closed_at`.** The URL point is already documented as intentional in `20261010040000`, because the URL may be a pre-filled "new issue" link. The state is also implied by `closed_at` being non-null, as GitHub reports it.
- **`github_installations.account_login` and `account_type` depend on `account_id`.** This is fine only if `account_id` is a candidate key, which it is in practice (one installation per account per app). The schema doesn't declare it `not null unique`, so as written it's a transitive dependency.

**Fixes:**
- For #1, #3, #5 and #6, the computed value should either be a generated column or be dropped and read from its source. `hb_json_int` already exists for the JSON cases.
- For #2, #4 and #10, use the same composite-FK pattern as the rest of the schema, e.g. `(item_id, project_id) → items(id, project_id)`.
- For #7, either keep `model` as the full `provider:model` string or generate `provider` from it.
- For #8, either refresh the title on read, or keep only the address and the id.
- For #9, move the post into its own table (`posts`: project, platform, external_id, url, title, text) and have items reference it.

---

## B. Not in 3NF on paper, kept consistent by Postgres

These are formally transitive (or partial) dependencies. Postgres computes the value or makes a disagreeing copy impossible, so they can't drift. They were kept on purpose for RLS and indexing.

**Copies of `project_id`, checked by composite foreign keys:**

| Table | Dependency |
|---|---|
| `items` | `person_id → project_id`; `account_id → project_id, platform` |
| `identities` | `person_id → project_id` |
| `touches` | `person_id → project_id`; `item_id → project_id, person_id` |
| `document_chunks` | `document_id → project_id` |
| `documents`, `project_memory` | `theme_id → project_id` (when `theme_id` is set) |
| `idea_items` | `idea_id → project_id`. The key is `(idea_id, item_id)`, so this depends on **part of the key**, which also breaks 2NF. It's the same argument that got `idea_items.person_id` dropped. Here it's kept for RLS and enforced by `idea_items_idea_fkey`. |

**Generated columns (a non-key column determines another):**

| Table | Generated columns | From |
|---|---|---|
| `items` | `triage_route`, `triage_kind`, `triage_action`, `triage_confidence`, `triage_summary` | `triage` |
| `drafts` | `tokens_in`, `tokens_out` | `tokens` |
| `documents` | `is_public` | `label` |
| `projects` | `url_key` | `url` (via `hb_url_key`) |

---

## C. Look like violations, but aren't 3NF violations

- **`voice_samples.text_sha256`.** `text → text_sha256` holds, but `(founder_id, text_sha256)` is declared unique, which makes it a candidate key. So `text_sha256` is a prime column, and 3NF allows a dependency on a prime column. It breaks BCNF but not 3NF.
- **Copies across tables, such as `people.first_touch_at`/`last_touch_at` (from `touches`), `ideas.asked_by` (from `idea_items` and `items`), `items.status` `draft_ready`/`answered` (from `drafts`), and `ideas.quote` (the first `idea_items.quote`).** These are aggregates or copies from other tables. They're denormalized, but normal forms are judged one table at a time, so they're not 3NF violations. The first two are maintained by triggers.
- **`source_syncs.source` (`'github:<repo>'`), and JSON or array columns such as `github_installations.repos`, `projects.links`, `projects.topics` and `items.thread`.** Whether these values are atomic is a 1NF question, not 3NF.
- **`projects.settings->'draft_model'` and `projects.knowledge_sources`.** These are dead data that the server no longer reads. That's a cleanup item, not a normal-form issue.
