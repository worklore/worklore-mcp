# What in the Hearback Schema Isn't in 3NF

Audited against Codd (1970), Fagin (1977), and Kent's 1983 rule (*every non-key column is a fact about the key, the whole key, and nothing but the key*), following the three-step check in the guide:

1. **Composite keys (2NF — "the whole key"):** columns on composite-keyed tables that depend on only part of the key.
2. **Copies of a parent (3NF — "nothing but the key"):** child columns that repeat a parent's attribute across a foreign key, or non-key columns that depend on another non-key entity embedded in the same row.
3. **Hand-written derived values (3NF):** columns computed in Edge Functions (`supabase/functions/`) from other columns in the same row or across rows without a generated column or trigger.
4. **1NF ("the key"):** arrays or JSONB columns that are relations in disguise and searched inside by queries or server code.

Migration `20261010040000_normal_forms.sql` already fixed the first wave of 1NF/2NF/3NF issues (`idea_items.person_id`, `document_chunks.{kind, source_url, source_ref, label}`, `plans.allowed_models` → `plan_models`, `documents.is_public`, `drafts.tokens_in`/`tokens_out`, `people.first_touch_at`/`last_touch_at`, and composite FKs on pre-existing `project_id` copies).

However, **later migrations (`20261011010000` through `20261015010000`) reintroduced several of the exact same patterns without database enforcement**, and several earlier tables still carry unenforced copies or hand-written derived columns.

Below is the complete audit, split into:
- **Part 1: Unenforced violations ("Has the problem")** — copies, transitive dependencies, partial dependencies, and hand-written derived values that Postgres does **not** keep consistent itself.
- **Part 2: Database-enforced denormalizations ("Mixed approach, not textbook 3NF")** — columns that violate textbook 2NF/3NF on paper, but are intentionally kept for RLS/indexing/speed and enforced by composite foreign keys, `GENERATED ALWAYS AS (...) STORED` columns, or triggers (including two subtle trigger gaps).
- **Part 3: Read-only verification queries & recommended fixes** for each unenforced violation.

---

## Part 1: Unenforced Violations ("Has the problem")

### 1. Composite Keys — 2NF ("the whole key")

| Table & Key | Column | Depends on | Where written / read | Recommended move |
| :--- | :--- | :--- | :--- | :--- |
| `idea_items`<br>`PRIMARY KEY (idea_id, item_id)`<br>(`20261008230200_backend_v1.sql:90-98`) | `quote` (`text`) | `item_id` alone (`firstSentence(items.text, 220)`) | Written in `_shared/core/ideas.ts:58,67`. Read in `github/index.ts:239` as `r.items!.text \|\| r.quote \|\| ""` (`items.text` is `NOT NULL`, so `r.quote` is never even used when `items` is joined). | **Drop the copy and join `items`:** drop `idea_items.quote` (or read `items.text` through `item_id`, as `github/index.ts` already does). |

*(Note: `idea_items.project_id` also depends on `idea_id` alone and on `item_id` alone, violating textbook 2NF, but it is enforced by composite foreign keys added in `20261010040000_normal_forms.sql:59-63`; see Part 2.)*

---

### 2. Copies of a Parent & Transitive Dependencies — 3NF ("nothing but the key")

#### 2a. Child columns copying a parent row without a composite FK or join

| Child table → Parent | Copied column(s) | How it can drift | Recommended move |
| :--- | :--- | :--- | :--- |
| `code_questions` → `items`<br>(`20261015010000_ask_code_model_calls.sql:56-60`) | `project_id` (copied from `items.project_id` when `item_id is not null` in `ask-code/index.ts:29-32`) | `code_questions` has separate single-column FKs `project_id references projects(id)` and `item_id references items(id) on delete set null`. Unlike `touches` and `idea_items`, it has **no composite FK** `(item_id, project_id) references items (id, project_id)`, so a question can reference an `item_id` from a different project. | **Add a composite FK:**<br>`foreign key (item_id, project_id) references items (id, project_id) on delete set null (item_id)`. |
| `model_calls` → `items` and `code_questions`<br>(`20261015010000_ask_code_model_calls.sql:15-24`) | `project_id`, `founder_id`, `item_id` (determined by `item_id` and by `run_id = code_questions.id`) | When `item_id` is set, `project_id` is `items.project_id` (no composite FK). When `run_id` is set (`ask_code.ts:68`), `project_id`, `item_id`, and `founder_id` duplicate `code_questions.{project_id, item_id, asked_by}` (and `run_id` has no FK to `code_questions.id`). In addition, `20261015010000_ask_code_model_calls.sql:40-43` backfilled `drafts` rows into `model_calls`, duplicating `(created_at, item_id, provider, model, tokens_in, tokens_out, tokens, latency_ms)` across both tables. | **Composite FK** `(item_id, project_id) references items (id, project_id) on delete set null (item_id)` (or read `project_id`/`item_id` via `run_id` / `item_id`). |
| `document_chunks` → `documents`<br>(`20261008230100_knowledge_chunks.sql:22-43`, `20261010040000_normal_forms.sql:128-129`) | `published_at`, `published_precision`, and the document title prefix in `title` (`"<doc.title> › <section>"`) | `20261010040000_normal_forms.sql` dropped `kind`, `source_url`, `source_ref`, and `label` from `document_chunks`, but left `published_at` and `published_precision` on the assumption that chunks can be dated per line. In `_shared/server/knowledge.ts:87-108` (`storeDocs`), both columns are written identically from the parent document on every chunk (`RawChunk` in `_shared/draft/chunk.ts:8-13` has no date field). And `chunk.ts:76` bakes `documents.title` into every `document_chunks.title`. | Either **drop `published_at` and `published_precision` from `document_chunks`** and read `d.published_at, d.published_precision` in `match_document_chunks()` (which already joins `documents d`), or only store a per-chunk override when git blame actually differs from the document's date. |
| `touches` → `items`, `drafts`, `ideas`<br>(`20261008170000_init.sql:194-208`) | `platform`, `kind`, `occurred_at`, `url`, `text`, `by_founder`, `meta` | `20261010040000_normal_forms.sql:48-53` added a composite FK on `(item_id, project_id, person_id)`, but `touches` still copies:<br>• Incoming item touches (`_shared/core/store.ts:89-94`): `platform`, `kind`, `occurred_at` (`items.posted_at`), `url` (`items.url`), `text` (`items.text`).<br>• Outgoing reply touches (`record_draft_outcome`, `20261011010000_draft_checks.sql:61-63`): `platform`, `occurred_at` (`drafts.posted_at`), `url` (`drafts.posted_url`), `text` (`drafts.final_text`), `by_founder` (`drafts.posted_by`).<br>• Issue touches (`github/index.ts:331-335`): `url` (`ideas.github_issue_url`), `text` (from `ideas.title` + `github_issue_number`), and `meta: {idea_id, repo, issue_number}`. | For touches linked to an `item_id` (or `draft_id` / `idea_id`), **read `url`, `text`, `platform` through the join** or keep `touches`synced via trigger when `items.text` / `items.url` is enriched (`store.ts:103`). |
| `voice_samples` → `drafts` + `items`<br>(`20261010010000_sources_voice_knowledge.sql:11-33,82-104`) | `founder_id`, `project_id`, `platform`, `source_url`, `text`, `context`, `posted_at` (when `source = 'hearback'`, `external_id = 'draft:<uuid>'`) | Trigger `hb_voice_from_draft()` and `backfillPosted()` (`_shared/core/sources/run.ts:100-119`) copy a posted draft's `final_text`, `posted_url`, `posted_at`, `posted_by`/`decided_by`, and its item's `project_id`, `platform`, `left(items.text, 600)` into `voice_samples` (so every posted reply is stored in **three** tables: `drafts`, `touches`, and `voice_samples`) with no FK to `drafts(id)`. | Add `draft_id uuid references drafts(id) on delete set null` (instead of encoding `'draft:' \|\| id` in `external_id`) or read draft attributes via join. |
| `people` ↔ `identities`<br>(`20261008170000_init.sql:108-137`) | `people.display_name`, `people.avatar_url` | `_shared/core/store.ts:31-46` (`upsertPerson`) copies `display_name` and `avatar_url` from the identity's platform profile onto `people`. | Intentional if `people.display_name` is a founder-editable override, otherwise read from `identities`. |
| `projects` ↔ `project_members`<br>(`20261008170000_init.sql:47,51-57,288-297`) | `projects.created_by` vs `project_members (role = 'owner')` | `add_creator_as_owner()` copies `created_by` into `project_members` on insert, but `_shared/server/ctx.ts:68-72` (`projectFounder`), `_shared/core/sources/run.ts:210,249`, and RLS policy `creator_reads` (`20261008230500_project_creator_read.sql:6`) read `projects.created_by` directly. If ownership changes or the creator leaves `project_members`, `created_by` and `project_members` disagree. | Read the owner from `project_members where role = 'owner'` (or enforce with a foreign key `foreign key (id, created_by) references project_members (project_id, founder_id)`). |

#### 2b. Transitive dependencies within a single table (`key → non-key determinant → non-key attribute`)

1. **`projects`: GitHub Projects v2 board attributes (`20261014010000_github_board_results.sql:17-24`)**
   - **Columns:** `github_board_id`, `github_board_owner`, `github_board_number`, `github_board_title`.
   - **Violation:** As the migration comment notes (`owner + number is the board's address; id is its GraphQL node id; title is GitHub's, cached for display`), the functional dependencies are:
     $$\text{projects.id} \to \text{github\_board\_id} \leftrightarrow (\text{github\_board\_owner}, \text{github\_board\_number}) \to \text{github\_board\_title}$$
     `github_board_title`, `github_board_owner`, and `github_board_number` are facts about the **GitHub board** (`github_board_id`), not about `projects.id`. If two Hearback projects in the same GitHub organization link the same organization board (`github/index.ts:184-186`), both rows duplicate the board's owner, number, and title, and refreshing one project's board title leaves the other stale.
   - **Recommended move:** Extract `github_boards (id text primary key, owner text not null, number int not null, title text not null, unique (owner, number))` and keep only `github_board_id text references github_boards(id)` on `projects` (or drop `github_board_title` and read it from GitHub when listing boards).

2. **`ideas`: GitHub issue & board status attributes (`20261008230200_backend_v1.sql:83-84`, `20261010030000_github_app.sql:64`, `20261014010000_github_board_results.sql:27-38`)**
   - **Columns:** `github_issue_repo`, `github_issue_number`, `github_issue_url`, `github_issue_state`, `github_issue_state_reason`, `github_issue_closed_at`, `github_board_status`, `github_checked_at`, `result_note`, `result_note_url`, `result_links`.
   - **Violation:**
     $$\text{ideas.id} \to (\text{github\_issue\_repo}, \text{github\_issue\_number}) \to (\text{github\_issue\_url}, \text{github\_issue\_state}, \text{github\_issue\_state\_reason}, \text{github\_issue\_closed\_at}, \text{github\_board\_status}, \text{github\_checked\_at})$$
     In `github/index.ts:366-383` (`comment_issue`), an idea can be attached to an **existing** GitHub issue `(github_issue_repo, github_issue_number)`. All issue state columns are facts about that GitHub issue, not about the idea itself; two ideas linked to the same issue number can hold conflicting `github_issue_state` / `github_board_status` values.
     Furthermore:
     - When `github_issue_repo` and `github_issue_number` are set, `github_issue_url` is deterministically `'https://github.com/' || github_issue_repo || '/issues/' || github_issue_number` (the only reason `20261010040000_normal_forms.sql:13-14` kept `github_issue_url` is that before an issue exists, the app may store a pre-filled `github.com/.../issues/new?...` URL in the same column, forcing `github/index.ts:309,343` to regex-parse `issueNumberFromUrl(idea.github_issue_url)`).
     - Unlike `projects_github_board_whole`, `ideas` has no `CHECK` constraint ensuring `github_issue_number` and `github_issue_repo` are null/non-null together, or that `github_issue_state` / `github_issue_closed_at` are null when `github_issue_number is null`.
   - **Recommended move:** Separate the pre-filled new-issue draft URL (or compute it on the fly) so `github_issue_url` is generated from `(github_issue_repo, github_issue_number)`, add a `CHECK` constraint that `(github_issue_number is null) = (github_issue_repo is null)`, or extract `github_issues (repo, number, state, state_reason, closed_at, board_status, checked_at, primary key (repo, number))`.

3. **`github_installations`: GitHub account attributes (`20261010030000_github_app.sql:9-21`)**
   - **Columns:** `account_id`, `account_login`, `account_type`.
   - **Violation:** `installation_id → account_id → (account_login, account_type)`. `account_login` and `account_type` (`'User' | 'Organization'`) are facts about the GitHub account (`account_id`), not the installation.

4. **`items`: Repeated article/post snapshot in `my_post` (`20261008170000_init.sql:154`)**
   - **Column:** `items.my_post` (`{url, title, text, author, is_owner}`).
   - **Violation:** `items.id → (my_post->>'url') → (my_post->>'title', my_post->>'text', my_post->>'author', my_post->>'is_owner')`. Every comment under the same dev.to article or Bluesky post repeats the post's title, author, and full body text. When `_shared/core/store.ts:102-115` (`richerContext`) updates one item with a fuller article body, other items under the same `my_post->>'url'` retain the truncated body (and the founder's own articles are already stored in `documents`).

---

### 3. Hand-Written Derived Values — 3NF (Same-Row & Cross-Row Functions)

#### 3a. Functions of other columns in the **same row** (written by hand in Edge Functions instead of `GENERATED ALWAYS AS (...) STORED`)

| Table | Derived column(s) | Deterministic source in the same row | Where written by hand (and how it breaks) | Recommended move |
| :--- | :--- | :--- | :--- | :--- |
| `model_calls`<br>(`20261015010000_ask_code_model_calls.sql:28-31`) | `tokens_in`, `tokens_out`, `cost_usd` | `usage` JSONB (`{input, output, cache_read, cache_write, cost_usd}`) | **The exact same bug `20261010040000_normal_forms.sql` fixed on `drafts`, reintroduced 5 days later.** Written by hand in `_shared/server/models.ts:46-50`, `_shared/server/ask_code.ts:88-93`, `_shared/server/models.ts:170-173`, and `20261015010000_ask_code_model_calls.sql:40-43`.<br>**Already disagrees in code:** In `_shared/draft/providers/gemini.ts:70-78`, `tokens_in` is `promptTokenCount` while `usage` sets `{input: promptTokenCount, cache_read: cachedContentTokenCount}`, and when output tokens are `0`, `tokens_out` is `0 \|\| null` (`null`) while `usage.output` is `0`. | Convert `tokens_in`, `tokens_out`, and `cost_usd` on `model_calls` to `GENERATED ALWAYS AS (...) STORED` using `hb_json_int(usage->>...)` (matching `drafts`). |
| `code_questions`<br>(`20261015010000_ask_code_model_calls.sql:73-74`) | `cost_usd` | `usage->>'cost_usd'` | Written twice in `_shared/server/ask_code.ts:97-98`: `cost_usd: run.usage.cost_usd, usage: { ...run.usage, ... }`. On failure (`ask_code.ts:104-106`), `cost_usd` is updated to `spent` while `usage` is left `null`, so `cost_usd` and `usage->>'cost_usd'` disagree on failed runs. | Either **make `cost_usd` a generated column** from `usage->>'cost_usd'` (and populate `usage` on failure), or **drop `usage.cost_usd`** / compute `cost_usd` from `model_calls` via trigger. |
| `drafts`<br>(`20261008230200_backend_v1.sql:65`) | `checks` (`text[]`) | `text` (`[check: …]` placeholders in `drafts.text`) | Extracted from `drafts.text` by regex in `_shared/core/draft_run.ts:173` (`checksOf(...)`) and `:284` (`parseChecks(r.text)`). `draftChecks()` (`draft_run.ts:224-228`) doesn't even read `drafts.checks`—it re-parses `drafts.text` on read. If `drafts.text` is updated directly, `drafts.checks` is stale. | **Drop `drafts.checks`** (parse `drafts.text` on read as `draftChecks()` already does) or make it `GENERATED ALWAYS AS (...) STORED` via an `IMMUTABLE` SQL function over `text`. |
| `drafts`<br>(`20261008170000_init.sql:182-186`, `20261008230200_backend_v1.sql:68-69`) | `outcome` (`posted_as_is` vs `posted_edited`), `posted_by`, `posted_at` | `btrim(final_text) = btrim(text)`, `decided_by`, `decided_at` | In `_shared/core/actions.ts:48`, `outcome` is `text === draft.text.trim() ? "posted_as_is" : "posted_edited"`, but `record_draft_outcome` accepts `p_outcome` and `p_final_text` independently with no DB check. And in `record_draft_outcome` (`20261011010000_draft_checks.sql:47-52`), whenever `outcome in ('posted_as_is', 'posted_edited')`, `posted_by` equals `decided_by` (`uid`) and `posted_at` equals `decided_at` (`now()`). | Add a `CHECK` constraint enforcing `outcome`/`final_text`/`posted_*` consistency, or derive `posted_as_is` vs `posted_edited` inside `record_draft_outcome` from `btrim(p_final_text) = btrim(d.text)` and drop `posted_by`/`posted_at` in favor of `decided_by`/`decided_at`. |
| `items`<br>(`20261008230100_knowledge_chunks.sql:108`, `20261008230200_backend_v1.sql:49-56`) | `triage` (when `origin = 'discover'`) | `discovery` JSONB (`discoveryTriage(discovery)`) | For `origin = 'discover'` items, `triage` (and therefore all 5 generated `triage_*` columns) is a pure function `discoveryTriage(discovery)` (`_shared/core/triage_run.ts:33-46`), written by hand in `discover/index.ts:143` (as a second `UPDATE` after `insertItem`) and `triage_run.ts:55-56`. | Compute `discoveryTriage` in SQL (trigger or generated expression when `origin = 'discover'`). |
| `voice_samples`<br>(`20261010010000_sources_voice_knowledge.sql:22-27`) | `quality`, `status`, `reason` | `scores` JSONB (`{p_meaningful, quality, decider, model}`) | In `_shared/core/sources/voice.ts:93-101` (`verdictFrom`) and `run.ts:135-137`, `quality` is `(scores->>'quality')::real` (or `0` when rejected by a rule), and when `scores is not null`, `status` (`p_meaningful >= 0.5 and quality >= 1.5`) and `reason` are deterministic functions of `scores`. | Make `quality` `GENERATED ALWAYS AS (coalesce((scores->>'quality')::real, case when status = 'rejected' then 0 end)) STORED` (or drop `scores.quality`). |
| `voice_samples`<br>(`20261010010000_sources_voice_knowledge.sql:22,91-94`) | `text_sha256` | `text` (`encode(digest(regexp_replace(btrim(text), '\s+', ' ', 'g'), 'sha256'), 'hex')`) | `20261010040000_normal_forms.sql:17-18` left `text_sha256` hand-written citing JS whitespace rules, yet the DB trigger `hb_voice_from_draft()` (`20261010010000_sources_voice_knowledge.sql:91-94`) **already** computes it in SQL with `regexp_replace(trim(new.final_text), '\s+', ' ', 'g')`! Because it is a plain column, any `UPDATE` to `voice_samples.text` leaves `text_sha256` wrong. | Make `text_sha256` `GENERATED ALWAYS AS (encode(extensions.digest(regexp_replace(btrim(text), '\s+', ' ', 'g'), 'sha256'), 'hex')) STORED`. |
| `document_chunks`<br>(`20261008230100_knowledge_chunks.sql:44-45`) | `content_sha256`, `tokens` | `title`, `content` | In `_shared/server/knowledge.ts:99,106`, `content_sha256` is `sha256(title \|\| '\n' \|\| content)` and `tokens` is `estimateTokens(content)` (`_shared/draft/chunk.ts:76`). Neither is enforced by Postgres if `title` or `content` is updated. | Make `content_sha256` a generated column `encode(extensions.digest(title \|\| E'\n' \|\| content, 'sha256'), 'hex')`. |
| `projects`<br>(`20261008230200_backend_v1.sql:8-14`) | `landing` JSONB | `name`, `one_liner`, `audience`, `topics`, `competitors`, `aims`, `url` | `read-landing/index.ts:75-80` writes the model's extracted fields to both top-level columns on `projects` and into `projects.landing`. Editing the project's profile columns leaves `projects.landing` with stale copies. | **Drop `projects.landing`** (it is never read by any Edge Function after `read-landing` writes it) or keep only `{source, final_url, html_title}` in `landing`. |
| `identities`<br>(`20261008170000_init.sql:130-133`) | `profile_url` | `platform`, `handle` | Written by hand as `https://bsky.app/profile/${handle}` or `https://dev.to/${handle}` (`bluesky/connector.ts:42`, `discover/index.ts:66,84`). | Compute from `(platform, handle)` in a helper/generated column or drop if unused. |
| `code_questions`<br>(`20261015010000_ask_code_model_calls.sql:69`) | `sources[].url` | `repo`, `commit_sha`, `sources[].path`, `start_line`, `end_line` | `_shared/askcode/agent.ts:121` writes `url: blobUrl(repo, sha, path, a, b)` into every element of `sources` JSONB. | Compute `blobUrl` on read from `repo`, `commit_sha`, and `{path, start_line, end_line}`. |

#### 3b. Cross-table derived values & aggregates written by hand in server code (no trigger)

| Table & Column(s) | What it aggregates / caches | How it is written (and where it drifts) | Recommended move |
| :--- | :--- | :--- | :--- |
| `code_questions`<br>`steps`, `usage`, `cost_usd`, `model`<br>(`20261015010000_ask_code_model_calls.sql:71-74`) | Aggregates of `model_calls` where `run_id = code_questions.id`:<br>• `steps = count(*)`<br>• `cost_usd = sum(cost_usd)`<br>• `usage.{input, output, cache_read, cache_write}` = sums over steps | In `_shared/server/ask_code.ts:88-107`, each step inserts a `model_calls` row with `run_id = id`.<br>• On success (lines 95-100), app code writes in-memory sums `steps`, `usage`, `cost_usd`.<br>• **On failure (lines 104-106), app code does a read-then-write** `select("cost_usd").eq("run_id", id)` to update `cost_usd`, **but forgets to update `steps` or `usage`**, leaving `steps = null` and `usage = null` even when steps ran and spent tokens! | **Trigger as sole writer** on `model_calls` (when `run_id is not null`) updating `code_questions.{steps, cost_usd, usage}`, or compute in a view joining `model_calls`. |
| `documents.content`<br>(`20261008170000_init.sql:232`) | Concatenation of `document_chunks.content` (`order by ord`) | `_shared/server/knowledge.ts:91` sets `documents.content = raw.map((c) => c.text).join("\n\n")` while inserting the individual chunks into `document_chunks.content` (minus privacy-dropped chunks, so `documents.content` can even contain chunks that line 98 dropped for privacy!). `documents.content` is never read anywhere in `supabase/functions/`. | **Drop `documents.content`** (or reconstruct from `document_chunks` ordered by `ord` if ever needed). |
| `items.status`<br>(`20261008170000_init.sql:156`) | Function of child `drafts.outcome` and `items.spam_verdict` | Updated across 6 places (`storeDraft` in `draft_run.ts:210`, `record_draft_outcome`, `triageAndRoute` in `triage_run.ts:96,103,108`, `markAnswered`/`markHidden` in `pipeline.ts:22,28`, and client updates for `spam_verdict`). No DB constraint or trigger prevents `status = 'draft_ready'` when no undecided draft exists, or `spam_verdict = 'spam'` while `status <> 'skipped'`. | Maintain `items.status` via a trigger on `drafts` and `items.spam_verdict` (plus a `CHECK (spam_verdict is distinct from 'spam' or status = 'skipped')`). |
| `ideas.status`<br>(`20261008230200_backend_v1.sql:82`) | Function of `github_issue_number`, `github_issue_state`, `github_issue_state_reason`, `github_board_status`, `result_drafted_at` | Updated in `github/index.ts:320` (`status: "issue_open"`), `_shared/server/github_results.ts:62` (`ideaStatusFor`), and `github_results.ts:113` (`status: "done"` when setting `result_drafted_at`). Nothing in the DB stops `result_drafted_at is not null` with `status <> 'done'` or `status = 'issue_open'` with `github_issue_number is null`. | Add a `CHECK` constraint (e.g. `(status <> 'issue_open' or github_issue_number is not null) and (result_drafted_at is null or status = 'done')`). |
| `voice_samples.active`<br>(`20261010010000_sources_voice_knowledge.sql:27`) | Cached top-30 diversity selection over `voice_samples` where `status = 'accepted'` | Computed in JS (`_shared/core/sources/run.ts:155-167`, `refreshActive`). There is **no `CHECK (not active or status = 'accepted')` constraint**; `refreshActive` has to run a manual cleanup query `.neq("status", "accepted").eq("active", true)`. Meanwhile `source_summary()` (`20261010020000_source_summary_branch.sql:9`) counts `filter (where active)` while `loadDraftRequest()` (`_shared/draft/load.ts:52`) filters `status = 'accepted' and active = true`. | Add `alter table voice_samples add constraint voice_samples_active_accepted check (not active or status = 'accepted')`. |
| `accounts.settings->'devto_counts'` vs `source_syncs.state->'counts'` | Per-article comment counts `{[article_id]: comments_count}` | Both `_shared/connectors/devto/connector.ts:66,97` and `_shared/connectors/devto/sources.ts:57,98` cache the exact same dev.to article comment counts in two different tables. | Store article comment counts in one place. |
| `ideas.updated_at`, `voice_samples.updated_at`, `github_installations.updated_at` | Last-modified timestamp of the row | Unlike `people` (which has a `BEFORE UPDATE` trigger `people_updated`), these three tables rely on callers setting `updated_at` by hand—and several writers forget:<br>• `ideas`: forgotten in `github_results.ts:148,162` and in trigger `items_person_recount()` (`20261010040000_normal_forms.sql:87-93`).<br>• `voice_samples`: set in `judgePending` (`run.ts:136`), forgotten in `refreshActive` (`run.ts:163-166`). | Reuse a `BEFORE UPDATE` trigger (`new.updated_at := now()`) on `ideas`, `voice_samples`, and `github_installations`. |

---

### 4. First Normal Form — 1NF (Relations in Disguise / Composite Strings Searched Inside)

| Table & Column | What it stores | How queries / server code search inside it | Recommended move |
| :--- | :--- | :--- | :--- |
| `github_installations.repos` (`jsonb`)<br>(`20261010030000_github_app.sql:15`) | Array of repo objects: `[{full_name, private, default_branch, open_issues, pushed_at, description, archived, has_issues}]` | Searched in `_shared/server/github.ts:153,160` (`(i.repos ?? []).find((x) => sameRepo(x.full_name, repo))`) and filtered/sorted in `github/index.ts:91-92`. Because it is a JSONB array instead of a table, `projects.github_repo`, `ideas.github_issue_repo`, and `code_questions.repo` cannot reference it via a foreign key, and `default_branch` is duplicated in `source_syncs.state->>'branch'`. | **Child table `github_installation_repos`** `(installation_id, full_name, private, default_branch, open_issues, pushed_at, description, archived, has_issues, primary key (installation_id, full_name))`. |
| `drafts.sources` (`jsonb`)<br>(`20261008230200_backend_v1.sql:66`) | Array of cited knowledge chunks: `[{title, url, kind, published_at}]` | Built in `_shared/core/draft_run.ts:170-172` by copying `title`, `source_url`, `kind`, and `published_at` from the retrieved `document_chunks` / `documents`. | **Child link table `draft_sources`** `(draft_id, chunk_id, ord, primary key (draft_id, chunk_id))` referencing `document_chunks(id)`, reading `title, url, kind, published_at` via join. |
| `touches.meta->>'external_id'` (`jsonb`)<br>(`20261008170000_init.sql:207`) | Platform ID of an outgoing touch (plus `{idea_id, repo, issue_number, how}` for issue touches) | Searched in SQL by `_shared/core/store.ts:124`: `.eq("person_id", t.person_id).eq("meta->>external_id", ext).limit(1)` to deduplicate collector touches in app code without a column or unique index. | Promote `external_id text` (and `idea_id uuid references ideas(id)`) to top-level columns on `touches` with a partial unique index `unique (person_id, platform, external_id) where external_id is not null`. |
| `source_syncs.source` (`text`) & `source_syncs.state->>'branch'`<br>(`20261010010000_sources_voice_knowledge.sql:48-49`, `20261010020000_source_summary_branch.sql:20-21`) | Composite string key: `'devto:writing:yahhi'`, `'devto:articles:yahhi'`, `'github:owner/repo'`, `'landing'` | Although `20261010040000_normal_forms.sql:15-16` noted *"the database only compares it"*, `source_summary()` (`20261010020000_source_summary_branch.sql:20-21`) constructs it in SQL (`s.source = 'github:' \|\| lower(coalesce(p.github_repo, ''))`) and extracts `s.state->>'branch'`. It packs source kind + platform + handle/repo into one string, duplicating `accounts.(platform, handle)` and `projects.github_repo` with no FK cleanup when a handle or repo changes. | Split into structured columns (`kind`, `account_id references accounts(id) on delete cascade`) or read `default_branch` from `github_installation_repos`. |

---

## Part 2: Database-Enforced Denormalizations ("Mixed approach, not textbook 3NF")

As `20261010040000_normal_forms.sql` notes, several columns violate strict textbook 2NF/3NF (Kent's rule) because they copy a parent attribute or store a function of other columns, **but Postgres enforces them** via composite foreign keys, `GENERATED ALWAYS AS (...) STORED` columns, or triggers so application code cannot make them disagree:

### 1. Parent-column copies kept for RLS & hot indexes, enforced by composite FKs (`20261010040000_normal_forms.sql:23-72`)
Every child table below stores `project_id` (and on `items` / `touches`, `platform` or `person_id`) so RLS policies can call `is_member(project_id)` without joining the parent:
- `identities (person_id, project_id)` → `people (id, project_id)`
- `items (person_id, project_id)` → `people (id, project_id)`
- `items (account_id, project_id, platform)` → `accounts (id, project_id, platform)` *(Note: PostgreSQL's default `MATCH SIMPLE` skips this check when `account_id IS NULL` on `origin = 'discover'` items)*
- `touches (person_id, project_id)` → `people (id, project_id)`
- `touches (item_id, project_id, person_id)` → `items (id, project_id, person_id) ON UPDATE CASCADE` *(skipped when `item_id IS NULL`)*
- `document_chunks (document_id, project_id)` → `documents (id, project_id)`
- `idea_items (idea_id, project_id)` → `ideas (id, project_id)` and `idea_items (item_id, project_id)` → `items (id, project_id)` *(both 2NF partial dependency and 3NF parent copy, locked down by the pair of composite FKs)*
- `documents (theme_id, project_id)` → `themes (id, project_id)`
- `project_memory (theme_id, project_id)` → `themes (id, project_id)`

### 2. Same-row transitive dependencies enforced by `GENERATED ALWAYS AS (...) STORED`
- `projects.url_key` = `hb_url_key(url)` (`20261009150000_project_url_key.sql:29`, `20261009150100_url_key_bare_host.sql:4`)
- `items.triage_route` = `triage->>'route'` (`20261008230100_knowledge_chunks.sql:109`)
- `items.triage_kind` = `triage->>'kind'`, `items.triage_action` = `triage->>'suggested_action'`, `items.triage_confidence` = `(triage->>'confidence')::real`, `items.triage_summary` = `triage->>'summary'` (`20261008230200_backend_v1.sql:53-56`)
- `documents.is_public` = `(label = 'quotable')` (`20261010040000_normal_forms.sql:135`)
- `drafts.tokens_in` and `drafts.tokens_out` = `hb_json_int(...)` over `drafts.tokens` (`20261010040000_normal_forms.sql:195-198`, hardened in `20261011120000_tokens_generated_safe.sql:16-22`)

### 3. Cross-table derived caches enforced by triggers (plus two minor trigger gaps)
- **`ideas.asked_by`** (`count(distinct i.person_id)` over `idea_items join items`): maintained by `ideas_recount()` on `idea_items` and `items_person_recount()` on `items` (`20261010040000_normal_forms.sql:76-96`).
  - **Gap 1:** `idea_items_count` (`20261008230200_backend_v1.sql:113`) only fires `AFTER INSERT OR DELETE ON idea_items`. If a row in `idea_items` has its `idea_id` or `item_id` updated (`UPDATE idea_items SET ...`), neither `old.idea_id` nor `new.idea_id` is recounted.
  - **Gap 2:** `ideas_recount()` only recounts `coalesce(new.idea_id, old.idea_id)`, which handles `INSERT` and `DELETE`, but an `UPDATE` moving a row from `old.idea_id` to `new.idea_id` needs to recount both.
- **`people.first_touch_at` and `people.last_touch_at`** (`min(occurred_at)` / `max(occurred_at)` over `touches`): maintained by `touches_person_span()` (`20261010040000_normal_forms.sql:204-222`).

---

## Part 3: Read-Only Verification Queries & Migration Sketch

Following Step 4 of the guide, run these read-only queries against the live database first to count any existing rows that disagree before applying constraints or converting columns:

```sql
-- 1. code_questions whose project_id disagrees with their item's project_id
select count(*) as code_questions_project_mismatch
from code_questions q
join items i on i.id = q.item_id
where q.project_id is distinct from i.project_id;

-- 2. model_calls whose project_id disagrees with their item's or code_question's project_id
select count(*) as model_calls_item_project_mismatch
from model_calls m
join items i on i.id = m.item_id
where m.project_id is distinct from i.project_id;

select count(*) as model_calls_run_mismatch
from model_calls m
join code_questions q on q.id = m.run_id
where m.project_id is distinct from q.project_id
   or m.item_id is distinct from q.item_id;

-- 3. model_calls where tokens_in, tokens_out, or cost_usd disagree with usage JSON
select count(*) as model_calls_usage_mismatch
from model_calls
where usage is not null
  and (
    tokens_in is distinct from (
      case when coalesce(hb_json_int(usage->>'input'), hb_json_int(usage->>'cache_read'), hb_json_int(usage->>'cache_write')) is null then null
           else coalesce(hb_json_int(usage->>'input'), 0) + coalesce(hb_json_int(usage->>'cache_read'), 0) + coalesce(hb_json_int(usage->>'cache_write'), 0)
      end
    )
    or tokens_out is distinct from hb_json_int(usage->>'output')
    or cost_usd is distinct from nullif(usage->>'cost_usd', '')::numeric(12, 6)
  );

-- 4. code_questions where cost_usd or steps disagree with usage or model_calls
select count(*) as code_questions_cost_mismatch
from code_questions q
where (q.usage is not null and q.cost_usd is distinct from nullif(q.usage->>'cost_usd', '')::numeric(12, 6))
   or q.steps is distinct from (select count(*)::int from model_calls m where m.run_id = q.id);

-- 5. document_chunks where published_at or published_precision differ from their document
select count(*) as chunks_published_mismatch
from document_chunks c
join documents d on d.id = c.document_id
where c.published_at is distinct from d.published_at
   or c.published_precision is distinct from d.published_precision;

-- 6. voice_samples where quality disagrees with scores->>'quality', or active = true on non-accepted rows
select count(*) as voice_samples_inconsistent
from voice_samples
where (scores is not null and quality is distinct from (scores->>'quality')::real)
   or (active and status <> 'accepted')
   or text_sha256 is distinct from encode(extensions.digest(regexp_replace(btrim(text), '\s+', ' ', 'g'), 'sha256'), 'hex');

-- 7. ideas with inconsistent GitHub issue / status columns
select count(*) as ideas_issue_inconsistent
from ideas
where (github_issue_number is null) <> (github_issue_repo is null)
   or (github_issue_number is null and github_issue_state is not null)
   or (result_drafted_at is not null and status <> 'done');

-- 8. projects sharing a github_board_id with conflicting owner/number/title
select count(*) as board_conflicts
from projects a
join projects b on a.github_board_id = b.github_board_id and a.id < b.id
where a.github_board_owner is distinct from b.github_board_owner
   or a.github_board_number is distinct from b.github_board_number
   or a.github_board_title is distinct from b.github_board_title;
```
