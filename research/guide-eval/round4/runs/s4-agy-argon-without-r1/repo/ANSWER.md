# What in the Schema Isn't in 3NF

Under Codd's definitions (1970/1971) and Kent's formulation (*"every non-key field is a fact about the key, the whole key, and nothing but the key"*), a relation is in **Third Normal Form (3NF)** if and only if:
1. It is in **1NF** (every attribute is atomic — no repeating groups, arrays, or nested relations/objects).
2. It is in **2NF** (no non-prime attribute has a **partial dependency** on a proper subset of a candidate key).
3. It has no **transitive dependencies** (no non-prime attribute is determined by another non-prime attribute or non-superkey set of attributes, whether within the same table or across tables).

Migration [`20261010040000_normal_forms.sql`](supabase/migrations/20261010040000_normal_forms.sql) audited the schema as of `2026-10-10` using a deliberately pragmatic *"mixed approach, not textbook 3NF"*: it normalized `plans.allowed_models` into `plan_models`, dropped `idea_items.person_id` and four redundant columns on `document_chunks`, converted `documents.is_public` and `drafts.tokens_in`/`tokens_out` into stored generated columns, added triggers for `people.first_touch_at`/`last_touch_at` and `ideas.asked_by`, and added composite foreign keys to guard `project_id` copies on child tables.

However, the final schema is **not in textbook 3NF** for four reasons:
1. **Unconstrained 3NF violations** — both from **later migrations** ([`20261014010000_github_board_results.sql`](supabase/migrations/20261014010000_github_board_results.sql) and [`20261015010000_ask_code_model_calls.sql`](supabase/migrations/20261015010000_ask_code_model_calls.sql)) that reintroduced the same patterns `normal_forms.sql` had fixed, and from pre-existing intra-table and cross-table dependencies left to application code.
2. **2NF violations (partial dependencies)** on tables with composite candidate keys (`idea_items`, `document_chunks`).
3. **Guarded 3NF violations** kept intentionally for RLS, indexing, or query speed and enforced via composite foreign keys, triggers, or `GENERATED ALWAYS AS ... STORED` columns.
4. **1NF violations** (`text[]` arrays, `jsonb` nested relations and multi-field objects, and composite string keys).

---

## 1. Unconstrained 3NF Violations (Transitive & Derived Dependencies)

These columns depend on non-key attributes (within the same row or in another table) **without** generated columns, triggers, or composite foreign keys preventing drift.

### A. Introduced After `20261010040000_normal_forms.sql`

#### 1. `model_calls` ([`20261015010000_ask_code_model_calls.sql`](supabase/migrations/20261015010000_ask_code_model_calls.sql))
* **`usage` $\to$ `(tokens_in, tokens_out, cost_usd)` (intra-table transitive dependency)**:
  `normal_forms.sql` converted `drafts.tokens_in` and `drafts.tokens_out` into generated columns over `drafts.tokens` so they could not disagree. Five days later, `model_calls` added `tokens_in int`, `tokens_out int`, and `cost_usd numeric(12,6)` as **plain, writable columns** alongside `usage jsonb` (`{input, output, cache_read, cache_write, cost_usd}`).
  * In [`ask_code.ts`](supabase/functions/_shared/server/ask_code.ts#L90-L92), `tokens_in = input + cache_read + cache_write`, `tokens_out = output`, and `cost_usd = usage.cost_usd`.
  * In [`models.ts`](supabase/functions/_shared/server/models.ts#L48-L49) and the migration backfill (`20261015010000_ask_code_model_calls.sql:40-43`), the same values are written to both `usage` and the top-level columns.
* **`(model, usage)` $\to$ `cost_usd` (transitive dependency via list pricing)**:
  `cost_usd` is a deterministic function of `model` and the token counts in `usage` via `PRICES` ([`pricing.ts`](supabase/functions/_shared/draft/providers/pricing.ts)).
* **`model` $\to$ `provider` (intra-table transitive dependency)**:
  The model identifier (`claude-sonnet-5-5`, `gemini-3.1-flash-lite`, `jev-latest`) uniquely determines `provider` (`anthropic`, `gemini`, `typesafe`).
* **`item_id` $\to$ `project_id` (cross-table transitive dependency, unguarded)**:
  When `item_id IS NOT NULL`, `item_id` determines `project_id` (`items.project_id`). Unlike earlier tables in `normal_forms.sql`, `model_calls` has separate single-column FKs (`project_id references projects(id)` and `item_id references items(id)`) with **no composite FK** `(item_id, project_id) references items (id, project_id)`.
* **`run_id` $\to$ `(project_id, item_id, founder_id, purpose)` (cross-table transitive dependency)**:
  When `run_id IS NOT NULL`, it references a `code_questions.id` ([`ask_code.ts`](supabase/functions/_shared/server/ask_code.ts#L68)), which already records `project_id`, `item_id`, and `asked_by` (`founder_id`).
* **Duplication with `drafts`**:
  Every draft call logs a row in `model_calls` (and migration `20261015010000_ask_code_model_calls.sql:40-43` backfilled existing `drafts` into `model_calls`), duplicating `(created_at, provider, model, tokens_in, tokens_out, tokens/usage, latency_ms)` across `drafts` and `model_calls`.

#### 2. `code_questions` ([`20261015010000_ask_code_model_calls.sql`](supabase/migrations/20261015010000_ask_code_model_calls.sql))
* **`item_id` $\to$ `project_id` (cross-table transitive dependency, unguarded)**:
  `ask-code/index.ts:29-33` looks up `project_id` from `items` when `item_id` is supplied, and stores both `project_id` and `item_id` on `code_questions`. Because `code_questions` only has `item_id uuid references items(id) on delete set null` (no composite FK `(item_id, project_id) references items (id, project_id)`), `code_questions.project_id` can disagree with `items.project_id`.
* **`usage` $\to$ `cost_usd` (intra-table transitive dependency)**:
  On completion ([`ask_code.ts`](supabase/functions/_shared/server/ask_code.ts#L97-L98)), `cost_usd` is written both as a top-level column (`cost_usd: run.usage.cost_usd`) and inside `usage` (`usage: { ...run.usage, ... }`). On failure ([`ask_code.ts`](supabase/functions/_shared/server/ask_code.ts#L106)), `cost_usd` is updated while `usage` is left `NULL`.
* **Derived aggregates from `model_calls` (`id` $\to$ `steps`, `cost_usd`, `model`, `usage`)**:
  Each step of an `ask-code` run inserts a row into `model_calls` with `run_id = code_questions.id`. `code_questions.steps`, `code_questions.cost_usd`, `code_questions.model`, and the token sums in `code_questions.usage` (`input`, `output`, `cache_read`, `cache_write`, `cost_usd`) are unguarded aggregates over `model_calls WHERE run_id = code_questions.id` ([`agent.ts`](supabase/functions/_shared/askcode/agent.ts#L164-L171), [`ask_code.ts`](supabase/functions/_shared/server/ask_code.ts#L104-L106)).
* **`(repo, commit_sha, path, start_line, end_line)` $\to$ `sources[i].url`**:
  Inside `code_questions.sources`, each entry's `url` is deterministically computed by `blobUrl(repo, sha, path, start_line, end_line)` ([`agent.ts`](supabase/functions/_shared/askcode/agent.ts#L121)).

#### 3. `projects`: GitHub Board Columns ([`20261014010000_github_board_results.sql`](supabase/migrations/20261014010000_github_board_results.sql))
* **`github_board_id` $\leftrightarrow$ `(github_board_owner, github_board_number)` $\to$ `github_board_title` (transitive dependency)**:
  A GitHub Projects v2 board is an independent entity with GraphQL node ID `github_board_id` and natural key `(github_board_owner, github_board_number)`. `github_board_title` (and `github_board_owner`/`github_board_number` given `github_board_id`) is a fact about the **GitHub board**, not the Hearback `project` ([`github/index.ts`](supabase/functions/github/index.ts#L184-L186)). If multiple projects link the same organization board, its attributes are duplicated across `projects` rows and can drift.

#### 4. `ideas`: GitHub Issue & Issue-Result Columns ([`20261010030000_github_app.sql`](supabase/migrations/20261010030000_github_app.sql), [`20261014010000_github_board_results.sql`](supabase/migrations/20261014010000_github_board_results.sql))
* **`(github_issue_repo, github_issue_number)` $\to$ `(github_issue_url, github_issue_state, github_issue_state_reason, github_issue_closed_at, github_board_status, github_checked_at, result_note_url, result_note, result_links)`**:
  * A GitHub issue is identified by `(github_issue_repo, github_issue_number)`. Its state (`open`/`closed`), `state_reason`, `closed_at`, `board_status`, `checked_at`, and maintainer comment (`result_note_url`, initial `result_note`, and `result_links`) are facts about the **GitHub issue**, not the `idea` ([`github_results.ts`](supabase/functions/_shared/server/github_results.ts#L58-L63)).
  * Furthermore, `comment_issue` ([`github/index.ts`](supabase/functions/github/index.ts#L366-L383)) links an idea to an **existing** issue `(github_issue_repo, github_issue_number)`, so multiple `ideas` rows can point to the same GitHub issue and hold conflicting snapshots of its state and result.
  * When `github_issue_number IS NOT NULL`, `github_issue_url` is deterministically `https://github.com/<github_issue_repo>/issues/<github_issue_number>` (as noted in `normal_forms.sql:13-14`, it only holds an independent value when `github_issue_number IS NULL` and it stores a pre-filled `/issues/new` link).
  * Also within `ideas`, `github_issue_state = 'open'` implies `github_issue_closed_at IS NULL` (not enforced by a check constraint).

---

### B. Other Unconstrained Intra-Table & Cross-Table 3NF Violations

#### 5. `drafts` ([`20261008170000_init.sql`](supabase/migrations/20261008170000_init.sql), [`20261008230200_backend_v1.sql`](supabase/migrations/20261008230200_backend_v1.sql), [`20261011010000_draft_checks.sql`](supabase/migrations/20261011010000_draft_checks.sql))
* **`text` $\to$ `checks` (intra-table transitive dependency)**:
  `drafts.checks` (`text[]`) is computed in TypeScript by regex-matching `[check: ...]` spans inside `drafts.text` (`checksOf(text.match(/\[check:[^\]]*\]/gi) ?? [])` in [`draft_run.ts`](supabase/functions/_shared/core/draft_run.ts#L173) and [`draft_run.ts`](supabase/functions/_shared/core/draft_run.ts#L284)). It is stored as a regular column rather than derived on read (as `draftChecks()` in `draft_run.ts:224-228` already does via `parseChecks(d.text)`) or generated by Postgres.
* **`model` $\to$ `provider` (intra-table transitive dependency)**:
  `drafts.provider` (`'anthropic'` / `'gemini'`) is functionally determined by `drafts.model`.
* **`(outcome, decided_by, decided_at)` $\to$ `(posted_by, posted_at)` and `(outcome, text)` $\to$ `final_text`**:
  In `record_draft_outcome()` ([`20261011010000_draft_checks.sql`](supabase/migrations/20261011010000_draft_checks.sql#L45-L52)):
  * Whenever `outcome IN ('posted_as_is', 'posted_edited')`, `posted_by` is always set to `decided_by` (`uid`) and `posted_at` is always set to `decided_at` (`now()`).
  * Whenever `outcome NOT IN ('posted_as_is', 'posted_edited')`, `posted_by`, `posted_at`, `posted_url`, and `final_text` are `NULL`.
  * When `outcome = 'posted_as_is'`, `final_text` equals `btrim(text)` ([`actions.ts`](supabase/functions/_shared/core/actions.ts#L48)).
* **`drafts.sources` (`jsonb`) duplicates `document_chunks` / `documents`**:
  Stores `[{title, url, kind, published_at}]` copied from the cited knowledge chunks ([`draft_run.ts`](supabase/functions/_shared/core/draft_run.ts#L170-L172)) rather than referencing `document_chunks(id)` via a join table.
* **`drafts.lint` (`jsonb`)**:
  Deterministic function of `(text, item.text, target_words, fact_context)` computed by `lint()` ([`draft_run.ts`](supabase/functions/_shared/core/draft_run.ts#L179)).
* **`drafts.meta` and `drafts.tokens` internal transitive dependencies**:
  * `meta.based_on` stores `{draft_id, version}` ([`draft_run.ts`](supabase/functions/_shared/core/draft_run.ts#L289)), where `draft_id` $\to$ `version` (`drafts.version`).
  * `tokens.model_choice` stores `{requested, reason, founder_id, plan_id}` ([`draft_run.ts`](supabase/functions/_shared/core/draft_run.ts#L178)), where `founder_id` $\to$ `plan_id` (`founders.plan_id`).

#### 6. `items` ([`20261008170000_init.sql`](supabase/migrations/20261008170000_init.sql), [`20261008230100_knowledge_chunks.sql`](supabase/migrations/20261008230100_knowledge_chunks.sql), [`20261008230200_backend_v1.sql`](supabase/migrations/20261008230200_backend_v1.sql))
* **`discovery` $\to$ `triage` when `origin = 'discover'` (intra-table transitive dependency)**:
  For discovered posts, `items.triage` (and therefore all five generated `triage_*` columns) is computed deterministically from `items.discovery` by the pure function `discoveryTriage(discovery)` ([`triage_run.ts`](supabase/functions/_shared/core/triage_run.ts#L33-L46), [`discover/index.ts`](supabase/functions/discover/index.ts#L143)).
* **`my_post` (`jsonb`) repeats parent post attributes across items**:
  Every comment (`items` row) under the same founder post/article stores a snapshot `{url, title, text, author, is_owner}` of that post. Thus `my_post->>'url'` $\to$ `(my_post->>'title', my_post->>'text', my_post->>'author')` is repeated across all comments on the same post (requiring `richerContext()` in [`core/store.ts`](supabase/functions/_shared/core/store.ts#L108-L115) to patch individual rows when fuller context arrives).
* **`thread` (`jsonb`) repeats ancestor messages**:
  Stores `[{author, text, posted_at, is_owner}]` on each item, duplicating comments that exist on sibling/parent items in the same thread.

#### 7. `touches` ([`20261008170000_init.sql`](supabase/migrations/20261008170000_init.sql))
* **Unconstrained copies of `items`, `drafts`, and `ideas` fields**:
  While `normal_forms.sql` added a composite FK on `(item_id, project_id, person_id)`, the remaining columns on `touches` duplicate data from the source rows without constraints:
  * **Incoming touches** (`direction = 'in'`, [`core/store.ts`](supabase/functions/_shared/core/store.ts#L90-L93)): `item_id` $\to$ `(platform, kind, occurred_at, url, text)` are copied directly from `items.(platform, kind, posted_at, url, text)`.
  * **Outgoing reply touches** (`direction = 'out'`, `kind = 'reply'`, [`20261011010000_draft_checks.sql`](supabase/migrations/20261011010000_draft_checks.sql#L61-L63)): duplicate `drafts.(posted_at, posted_url, final_text, posted_by)` and `items.platform`.
  * **Outgoing issue touches** (`direction = 'out'`, `kind = 'issue'`, [`github/index.ts`](supabase/functions/github/index.ts#L331-L335)): `meta->>'idea_id'` $\to$ `(url, meta->>'repo', meta->>'issue_number', text)` duplicate `ideas.(github_issue_url, github_issue_repo, github_issue_number, title)`.

#### 8. `voice_samples` ([`20261010010000_sources_voice_knowledge.sql`](supabase/migrations/20261010010000_sources_voice_knowledge.sql))
* **`text` $\to$ `text_sha256` (intra-table transitive dependency)**:
  `text_sha256` is the SHA-256 of whitespace-normalized `text` ([`voice.ts`](supabase/functions/_shared/core/sources/voice.ts#L24-L29) and trigger `hb_voice_from_draft()` in `20261010010000_sources_voice_knowledge.sql:91-94`). Left as an ordinary column (noted in `normal_forms.sql:17-18`), so `id` $\to$ `text` $\to$ `text_sha256` is an unguarded transitive dependency, and candidate key `(founder_id, text_sha256)` is functionally determined by `(founder_id, text)`.
* **`scores` $\to$ `(quality, status, reason)` (intra-table transitive dependency)**:
  In `verdictFrom()` ([`voice.ts`](supabase/functions/_shared/core/sources/voice.ts#L93-L101)) and `judgePending()` ([`run.ts`](supabase/functions/_shared/core/sources/run.ts#L135-L137)):
  * `quality` is stored both in the column `voice_samples.quality` and inside `voice_samples.scores->>'quality'`.
  * For judged rows, `status` (`'accepted'` vs `'rejected'`) and `reason` are deterministic functions of `scores->>'p_meaningful'` and `quality` (or for rule-rejected rows, `ruleReject(text)` determines `status = 'rejected'`, `reason = 'rule: ...'`, `quality = 0`, `scores = null`).
  * `status <> 'accepted'` $\to$ `active = false` is maintained only in application code (`refreshActive()` in [`run.ts`](supabase/functions/_shared/core/sources/run.ts#L166)), with no `CHECK` constraint.
* **Cross-table duplication for `source = 'hearback'` (`external_id = 'draft:<uuid>'`)**:
  Trigger `hb_voice_from_draft()` (`20261010010000_sources_voice_knowledge.sql:82-104`) and `backfillPosted()` ([`run.ts`](supabase/functions/_shared/core/sources/run.ts#L100-L119)) copy `founder_id` (`posted_by`/`decided_by`), `project_id`, `platform`, `source_url` (`posted_url`), `text` (`final_text`), `context` (`left(items.text, 600)`), and `posted_at` from `drafts` and `items`. Thus a posted reply's text, URL, author, and timestamp live in **three** tables: `drafts`, `touches`, and `voice_samples`.

#### 9. `documents` and `document_chunks` ([`20261008230100_knowledge_chunks.sql`](supabase/migrations/20261008230100_knowledge_chunks.sql), [`20261010010000_sources_voice_knowledge.sql`](supabase/migrations/20261010010000_sources_voice_knowledge.sql))
* **`documents.content_sha256` and `document_chunks.content_sha256` / `tokens` (intra-table transitive dependencies)**:
  * On `documents`, `content_sha256` is computed in application code from `(kind, title, published_at, label, lang, markdown)` (`docSha` in [`knowledge.ts`](supabase/functions/_shared/server/knowledge.ts#L35-L36)).
  * On `document_chunks`, `content_sha256` is `sha256(title || "\n" || content)` and `tokens` is `estimateTokens(content)` (`Math.ceil(words(text) * 1.35)` in [`chunk.ts`](supabase/functions/_shared/draft/chunk.ts)), both stored as ordinary writable columns ([`knowledge.ts`](supabase/functions/_shared/server/knowledge.ts#L99-L106)).
* **`documents.content` vs `document_chunks.content` (cross-table redundancy)**:
  In `storeDocs()` ([`knowledge.ts`](supabase/functions/_shared/server/knowledge.ts#L91)), `documents.content` is written as `raw.map((c) => c.text).join("\n\n")`, duplicating the text stored across `document_chunks.content`.
* **`document_chunks.(published_at, published_precision, lang)` vs `documents`**:
  Although `normal_forms.sql:128-129` kept `published_at`, `published_precision`, and `lang` on `document_chunks` so chunks could in principle have per-section dates, `storeDocs()` ([`knowledge.ts`](supabase/functions/_shared/server/knowledge.ts#L90-L108)) writes the parent document's `published_at`, `published_precision`, and `lang` identically onto every chunk of that document (`document_id` $\to$ `published_at, published_precision, lang`).
* **`documents` rows copied from `code_questions`**:
  `useAnswer()` ([`ask_code.ts`](supabase/functions/_shared/server/ask_code.ts#L119-L129)) inserts a `documents` row with `url = 'hearback:code-answer/' || q.id`, duplicating `code_questions.(question, answer, details, repo, sources)`.

#### 10. `projects.landing` vs Top-Level `projects` Columns ([`20261008230200_backend_v1.sql`](supabase/migrations/20261008230200_backend_v1.sql))
* In [`read-landing/index.ts`](supabase/functions/read-landing/index.ts#L75-L80), `projects.landing` (`jsonb`) stores `{name, one_liner, audience, topics, competitors, aims, source, final_url, title}` at the same time those exact fields are written to `projects.(name, one_liner, audience, topics, competitors, aims, url)`. Later edits to the top-level columns leave `projects.landing` out of sync.

#### 11. `github_installations`, `identities`, `accounts`, and `people`
* **`github_installations`: `account_id` $\leftrightarrow$ `account_login` $\to$ `account_type`** ([`20261010030000_github_app.sql`](supabase/migrations/20261010030000_github_app.sql)):
  `account_login` and `account_type` (`'User'` | `'Organization'`) are facts about the GitHub account (`account_id`), transitively dependent on `installation_id`.
* **`identities`: `(platform, handle)` $\to$ `profile_url` (and external profile attributes across projects)** ([`20261008170000_init.sql`](supabase/migrations/20261008170000_init.sql)):
  `profile_url` is derived from `(platform, handle)` (e.g. `https://dev.to/<handle>`, `https://bsky.app/profile/<handle>` in [`discover/index.ts`](supabase/functions/discover/index.ts#L66-L84)), and if two projects interact with the same `(platform, handle)`, `external_id`, `profile_url`, and `public_profile` are duplicated per project.
* **`accounts`: `(platform, handle)` $\to$ `external_id`, `settings->>'pds'`** ([`20261008170000_init.sql`](supabase/migrations/20261008170000_init.sql)):
  If two projects connect the same platform account `(platform, handle)`, its platform `external_id` (e.g. Bluesky DID) and PDS URL (`settings.pds`) depend on `(platform, handle)` alone rather than `(project_id, platform, handle)`.
* **`people.(display_name, avatar_url)` vs `identities`** ([`core/store.ts`](supabase/functions/_shared/core/store.ts#L31-L45)) and **`founders.(display_name, avatar_url)` vs `auth.users`** ([`20261008170000_init.sql`](supabase/migrations/20261008170000_init.sql#L300-L306)):
  Copied on creation/upsert from the external identity or `auth.users.raw_user_meta_data`.

---

## 2. 2NF Violations (Partial Dependencies on Composite Candidate Keys)

Because 3NF requires 2NF, any non-prime attribute that depends on only part of a composite candidate key violates both 2NF and 3NF:

1. **`idea_items` — `PRIMARY KEY (idea_id, item_id)`** ([`20261008230200_backend_v1.sql`](supabase/migrations/20261008230200_backend_v1.sql), [`20261010040000_normal_forms.sql`](supabase/migrations/20261010040000_normal_forms.sql)):
   * **`idea_items.project_id`**: `normal_forms.sql` dropped `idea_items.person_id` because in a table keyed by `(idea_id, item_id)`, `person_id` depended on `item_id` alone (2NF violation). By the exact same rule, `idea_items.project_id` is a non-prime attribute that depends on `idea_id` alone (`ideas.project_id`) **and** on `item_id` alone (`items.project_id`). Even with composite FKs preventing disagreement, `idea_items.project_id` violates **2NF**.
   * **`idea_items.quote`** (and `ideas.quote`): In `fileFeedback()` ([`core/ideas.ts`](supabase/functions/_shared/core/ideas.ts#L58-L68)), `quote` is always `firstSentence(item.text, 220)`. It depends on `item_id` alone (`item_id` $\to$ `items.text` $\to$ `quote`), not on `(idea_id, item_id)` (and `ideas.quote` copies the first linked item's `quote`).

2. **`document_chunks` — Candidate Key `UNIQUE (document_id, ord)`** ([`20261008230100_knowledge_chunks.sql`](supabase/migrations/20261008230100_knowledge_chunks.sql), [`20261010040000_normal_forms.sql`](supabase/migrations/20261010040000_normal_forms.sql)):
   * **`document_chunks.project_id`**: The candidate keys of `document_chunks` are `{id}` and `{document_id, ord}`. `project_id` is a non-prime attribute determined by `document_id` alone (`document_id` $\to$ `documents.project_id`). Relative to `{document_id, ord}` this is a **2NF partial dependency**; relative to `{id}` it is a **3NF transitive dependency** (`id` $\to$ `document_id` $\to$ `project_id`).

3. **Superkey `UNIQUE` Constraints on Parent Tables** ([`20261010040000_normal_forms.sql`](supabase/migrations/20261010040000_normal_forms.sql#L25-L31)):
   * `people (id, project_id)`, `accounts (id, project_id, platform)`, `items (id, project_id)` and `(id, project_id, person_id)`, `documents (id, project_id)`, `ideas (id, project_id)`, and `themes (id, project_id)` declare composite `UNIQUE` constraints where `id` is already the `PRIMARY KEY`. Because `{id}` alone determines every column in those tables, those composite constraints are proper supersets of the key `{id}` added only to satisfy PostgreSQL's requirement that a composite FK target a matching unique index.

---

## 3. 3NF Violations Kept by Design (Guarded by Composite FKs, Triggers, or Generated Columns)

As documented in [`20261010040000_normal_forms.sql`](supabase/migrations/20261010040000_normal_forms.sql#L5-L10), the following attributes violate textbook 3NF (they are transitively derived from non-key columns or foreign rows) but are constrained by PostgreSQL so they cannot drift in normal operation:

### A. Child-Table Copies Guarded by Composite Foreign Keys
* **`items.project_id`**: `id` $\to$ `person_id` $\to$ `project_id` (and `id` $\to$ `account_id` $\to$ `project_id` when `account_id IS NOT NULL`).
* **`items.platform`** (when `account_id IS NOT NULL`): `id` $\to$ `account_id` $\to$ `platform` (guarded by `items_account_fkey (account_id, project_id, platform) references accounts (id, project_id, platform)`).
* **`identities.project_id`**: `id` $\to$ `person_id` $\to$ `project_id` (guarded by `identities_person_fkey`).
* **`touches.project_id`**: `id` $\to$ `person_id` $\to$ `project_id` (guarded by `touches_person_fkey`).
* **`touches.person_id`** (when `item_id IS NOT NULL`): `id` $\to$ `item_id` $\to$ `person_id` (guarded by `touches_item_fkey (item_id, project_id, person_id) references items (id, project_id, person_id) on update cascade`).
* **`document_chunks.project_id`**: `id` $\to$ `document_id` $\to$ `project_id` (guarded by `document_chunks_document_fkey`).
* **`idea_items.project_id`**: `(idea_id, item_id)` $\to$ `idea_id` $\to$ `project_id` and `item_id` $\to$ `project_id` (guarded by `idea_items_idea_fkey` and `idea_items_item_fkey`).
* **`documents.project_id`** (when `theme_id IS NOT NULL`): `id` $\to$ `theme_id` $\to$ `project_id` (guarded by `documents_theme_fkey`).
* **`project_memory.project_id`** (when `theme_id IS NOT NULL`): `id` $\to$ `theme_id` $\to$ `project_id` (guarded by `project_memory_theme_fkey`).

### B. Cached Aggregates Maintained by Triggers
* **`ideas.asked_by`**: Cached `COUNT(DISTINCT items.person_id)` over `idea_items JOIN items`, maintained by triggers `idea_items_count` (`AFTER INSERT OR DELETE ON idea_items`) and `items_person_recount` (`AFTER UPDATE OF person_id ON items`). *(Note: `idea_items_count` does not fire on `UPDATE OF idea_id, item_id ON idea_items`, and direct updates to `ideas.asked_by` are not blocked.)*
* **`people.first_touch_at` and `people.last_touch_at`**: Cached `MIN(occurred_at)` and `MAX(occurred_at)` from `touches`, maintained by trigger `touches_person_span` (`AFTER INSERT OR DELETE OR UPDATE OF person_id, occurred_at ON touches`).
* **`people.stage_changed_at`**: Cached timestamp of the most recent change to `people.stage`, maintained by trigger `people_updated` (`20261008230200_backend_v1.sql:38-44`).

### C. Stored `GENERATED ALWAYS AS` Columns (Intra-Table Transitive Dependencies)
* **`projects.url_key`**: `hb_url_key(url)` (`id` $\to$ `url` $\to$ `url_key`, `20261009150000_project_url_key.sql`).
* **`documents.is_public`**: `(label = 'quotable')` (`id` $\to$ `label` $\to$ `is_public`, `20261010040000_normal_forms.sql`).
* **`items.triage_route`, `triage_kind`, `triage_action`, `triage_confidence`, `triage_summary`**: Extracted from `items.triage` (`id` $\to$ `triage` $\to$ `triage_*`, `20261008230100_knowledge_chunks.sql`, `20261008230200_backend_v1.sql`).
* **`drafts.tokens_in`, `drafts.tokens_out`**: Summed/extracted from `drafts.tokens` (`id` $\to$ `tokens` $\to$ `(tokens_in, tokens_out)`, `20261010040000_normal_forms.sql`, `20261011120000_tokens_generated_safe.sql`).

---

## 4. 1NF Violations (Non-Atomic Attributes: Arrays, JSONB, Composite Strings)

Because $\text{3NF} \subset \text{2NF} \subset \text{1NF}$, attributes that store repeating groups, nested tables, multi-field records, or composite strings violate 1NF and therefore are not in 3NF:

### A. Array Columns (`text[]`)
* **`founders.languages`** (`text[] not null default '{en}'`)
* **`projects.languages`, `projects.audience`, `projects.topics`, `projects.competitors`** (`text[]` — `topics` is iterated in [`discover/index.ts`](supabase/functions/discover/index.ts#L60-L78) to run per-topic queries)
* **`drafts.checks`** (`text[]` — repeating list of `[check: ...]` questions, also derived from `drafts.text`)

### B. JSONB Columns Storing Nested Relations (Arrays of Objects)
* **`github_installations.repos`** (`[{full_name, private, default_branch, open_issues, pushed_at, description, archived, has_issues}]`) — a nested relation of GitHub repositories searched and filtered in [`server/github.ts`](supabase/functions/_shared/server/github.ts#L153) and [`github/index.ts`](supabase/functions/github/index.ts#L91-L92).
* **`projects.links`** (`[{title, url}]`)
* **`items.thread`** (`[{author, text, posted_at, is_owner}]`)
* **`drafts.sources`** (`[{title, url, kind, published_at}]`)
* **`drafts.meta`** (`resolved: [{check_id, question, action, answer, method, reason, by, at}]`)
* **`ideas.result_links`** (`[{title, url, kind}]`)
* **`code_questions.sources`** (`[{path, start_line, end_line, note, url}]`)

### C. JSONB Columns Packing Multiple Attributes / Sub-Objects
* **`items.triage`**, **`items.discovery`**, **`items.my_post`**, **`items.root_ref`**, **`items.parent_ref`**
* **`drafts.tokens`**, **`drafts.lint`**, **`drafts.meta`**
* **`model_calls.usage`**, **`code_questions.usage`**
* **`voice_samples.scores`** (`{p_meaningful, quality, decider, model}`)
* **`source_syncs.state`** (queried in SQL as `s.state->>'branch'` in [`20261010020000_source_summary_branch.sql`](supabase/migrations/20261010020000_source_summary_branch.sql#L20)), **`source_syncs.stats`**
* **`touches.meta`** (queried in [`core/store.ts`](supabase/functions/_shared/core/store.ts#L124) via `.eq("meta->>external_id", ext)`)
* **`identities.public_profile`**
* **`projects.landing`**, **`projects.settings`**, **`projects.knowledge_sources`** (unused legacy column)
* **`accounts.settings`**

### D. Composite / Structured String Columns
* **`source_syncs.source`**: Encodes `<platform>:<kind>:<handle>` or `github:<owner/repo>` (e.g. `'devto:writing:yahhi'`, `'github:owner/repo'`). Joined in [`20261010020000_source_summary_branch.sql`](supabase/migrations/20261010020000_source_summary_branch.sql#L21) by string concatenation: `s.source = 'github:' || lower(coalesce(p.github_repo, ''))`.
* **`voice_samples.external_id`**: Encodes `'draft:<uuid>'` or `'<repo>:<path>#<n>'` ([`20261010010000_sources_voice_knowledge.sql`](supabase/migrations/20261010010000_sources_voice_knowledge.sql#L17)).
* **`documents.url`** (for Ask-the-Code answers): Encodes `'hearback:code-answer/<code_questions.id>'` ([`ask_code.ts`](supabase/functions/_shared/server/ask_code.ts#L124)).
* **`plans.default_model`**, **`plan_models.model`**, **`founders.draft_model`**: Encode `<provider>:<model>` (e.g. `'anthropic:claude-sonnet-5-5'`, parsed by `parseModelSpec()`).
* **`document_chunks.embedding_model`**: Encodes `<model>@<dims>` (`'gemini-embedding-001@768'` in [`knowledge.ts`](supabase/functions/_shared/server/knowledge.ts#L140)).
* **`projects.github_repo`**, **`ideas.github_issue_repo`**, **`code_questions.repo`**: Encode `<owner>/<name>`.

---

## 5. Summary by Table

| Table | Non-3NF Elements (1NF / 2NF / 3NF) |
| :--- | :--- |
| **`founders`** | **1NF**: `languages` (`text[]`), `draft_model` (`"provider:model"`). **3NF**: `display_name`, `avatar_url` seeded from `auth.users`. |
| **`plans`** | **1NF**: `default_model` (`"provider:model"`). |
| **`plan_models`** | **1NF**: `model` (`"provider:model"`). |
| **`projects`** | **3NF (unguarded)**: `github_board_id` $\leftrightarrow$ `(github_board_owner, github_board_number)` $\to$ `github_board_title`; `landing` JSONB duplicates `name`, `one_liner`, `audience`, `topics`, `competitors`, `aims`, `url`. **3NF (generated)**: `url` $\to$ `url_key`. **1NF**: `languages`, `audience`, `topics`, `competitors` (`text[]`); `links`, `landing`, `settings`, `knowledge_sources` (`jsonb`); `github_repo` (`"owner/name"`). |
| **`accounts`** | **3NF**: `(platform, handle)` $\to$ `external_id`, `settings->>'pds'`. **1NF**: `settings` (`jsonb`). |
| **`themes`** | Conceptually overlaps with `project_memory` (`kind = 'position'`, noted in `normal_forms.sql:19`). |
| **`people`** | **3NF (trigger-cached)**: `first_touch_at`, `last_touch_at` (aggregates of `touches.occurred_at`); `stage_changed_at`. **3NF**: `display_name`, `avatar_url` copied from `identities`. |
| **`identities`** | **3NF (FK-guarded)**: `person_id` $\to$ `project_id`. **3NF (unguarded)**: `(platform, handle)` $\to$ `profile_url`, `external_id`, `public_profile`. **1NF**: `public_profile` (`jsonb`). |
| **`items`** | **3NF (FK-guarded)**: `person_id` $\to$ `project_id`; `account_id` $\to$ `(project_id, platform)`. **3NF (unguarded)**: `discovery` $\to$ `triage` (when `origin = 'discover'`); `my_post` repeats post `title`/`text` across comments on the same post; `thread` repeats ancestor comments. **3NF (generated)**: `triage` $\to$ `triage_route`, `triage_kind`, `triage_action`, `triage_confidence`, `triage_summary`. **1NF**: `root_ref`, `parent_ref`, `my_post`, `thread`, `triage`, `discovery` (`jsonb`). |
| **`drafts`** | **3NF (unguarded)**: `text` $\to$ `checks`; `model` $\to$ `provider`; `outcome` + `decided_by`/`decided_at` $\to$ `posted_by`/`posted_at`/`final_text`; `sources` copies chunk fields from `document_chunks`/`documents`; `lint` derived from `text`; `meta.based_on.draft_id` $\to$ `version`; `tokens.model_choice.founder_id` $\to$ `plan_id`. **3NF (generated)**: `tokens` $\to$ `tokens_in`, `tokens_out`. **1NF**: `checks` (`text[]`); `sources`, `lint`, `tokens`, `meta` (`jsonb`). |
| **`touches`** | **3NF (FK-guarded)**: `person_id` $\to$ `project_id`; `item_id` $\to$ `(project_id, person_id)`. **3NF (unguarded)**: copies `platform`, `kind`, `occurred_at`, `url`, `text` from `items` / `drafts` / `ideas`. **1NF**: `meta` (`jsonb`). |
| **`project_memory`** | **3NF (FK-guarded)**: `theme_id` $\to$ `project_id` (when `theme_id IS NOT NULL`). |
| **`documents`** | **3NF (FK-guarded)**: `theme_id` $\to$ `project_id` (when `theme_id IS NOT NULL`). **3NF (generated)**: `label` $\to$ `is_public`. **3NF (unguarded)**: document fields $\to$ `content_sha256`; `content` is concatenation of `document_chunks.content`; `ask_code` documents copy `code_questions`. |
| **`document_chunks`** | **2NF & 3NF (FK-guarded)**: `document_id` $\to$ `project_id` (partial dependency on `(document_id, ord)` and transitive on `id`). **3NF (unguarded)**: `(title, content)` $\to$ `content_sha256`; `content` $\to$ `tokens`; `published_at`, `published_precision`, `lang` copied per document in `storeDocs()`. **1NF**: `embedding_model` (`"model@dims"`). |
| **`ideas`** | **3NF (trigger-cached)**: `asked_by` (distinct `items.person_id` count). **3NF (unguarded)**: `(github_issue_repo, github_issue_number)` $\to$ `(github_issue_url, github_issue_state, github_issue_state_reason, github_issue_closed_at, github_board_status, github_checked_at, result_note_url, result_note, result_links)`; `quote` / `title` / `summary` copied from first item. **1NF**: `result_links` (`jsonb`); `github_issue_repo` (`"owner/name"`). |
| **`idea_items`** | **2NF & 3NF (FK-guarded)**: `idea_id` $\to$ `project_id` and `item_id` $\to$ `project_id` (partial dependency on composite key `(idea_id, item_id)`). **2NF & 3NF (unguarded)**: `item_id` $\to$ `quote` (`firstSentence(items.text, 220)`). |
| **`voice_samples`** | **3NF (unguarded)**: `text` $\to$ `text_sha256`; `scores` $\to$ `(quality, status, reason)`; `status` $\to$ `active`; `source = 'hearback'` rows copy `founder_id`, `project_id`, `platform`, `source_url`, `text`, `context`, `posted_at` from `drafts` + `items`. **1NF**: `scores` (`jsonb`), `external_id` (`"draft:<uuid>"`). |
| **`source_syncs`** | **1NF & 3NF**: `source` packs `<platform>:<kind>:<handle>` or `github:<repo>` (duplicates `accounts.handle` / `projects.github_repo`); `state`, `stats` (`jsonb`, `state->>'branch'` queried in SQL). |
| **`github_installations`** | **3NF (unguarded)**: `account_id` $\leftrightarrow$ `account_login` $\to$ `account_type`. **1NF**: `repos` (`jsonb` array of repository objects). |
| **`model_calls`** | **3NF (unguarded)**: `usage` $\to$ `(tokens_in, tokens_out, cost_usd)`; `(model, usage)` $\to$ `cost_usd`; `model` $\to$ `provider`; `item_id` $\to$ `project_id` (no composite FK); `run_id` $\to$ `(project_id, item_id, founder_id)`; duplicates `drafts` call metrics. **1NF**: `usage` (`jsonb`). |
| **`code_questions`** | **3NF (unguarded)**: `item_id` $\to$ `project_id` (no composite FK); `usage` $\to$ `cost_usd`; `steps`, `cost_usd`, `model`, `usage` are aggregates of `model_calls WHERE run_id = id`; `(repo, commit_sha, path, start_line, end_line)` $\to$ `sources[i].url`. **1NF**: `sources`, `usage` (`jsonb`); `repo` (`"owner/name"`). |
| **`project_members`**, **`project_invites`**, **`item_themes`**, **`waitlist`**, **`usage_counters`**, **`github_installation_projects`**, **`github_install_states`** | In 3NF (note: `usage_counters` is a daily request-cap counter; `projects.created_by` is seeded into `project_members` via trigger). |
