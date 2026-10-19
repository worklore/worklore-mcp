# Database Normalization Audit: 1NF, 2NF, and 3NF Analysis

This document audits the Supabase Postgres schema (`supabase/migrations`) and Deno server functions (`supabase/functions`) for Hearback following the criteria established in William Kent's 1983 paper (*"A Simple Guide to Five Normal Forms in Relational Database Theory"*):

> **"Every non-key attribute must provide a fact about the key, the whole key, and nothing but the key."**
>
> - **1NF:** Attributes must be atomic (no arrays or JSON encoding relations/repeating groups).
> - **2NF ("the whole key"):** No non-key attribute may depend on only a proper subset of a composite candidate key.
> - **3NF ("nothing but the key"):** No non-key attribute may depend on another non-key attribute (no transitive dependencies), including redundant copies of parent attributes and hand-written derived values that are not kept consistent by the database.

---

## 1. Executive Summary of Findings

Across the schema's evolution, violations fall into two categories:
1. **Historical violations** (present in initial migrations up to October 9, 2026, and addressed in `20261010040000_normal_forms.sql`).
2. **Current / reintroduced violations** (introduced in migration `20261015010000_ask_code_model_calls.sql` on October 15, 2026 for the "Ask the code" feature).
3. **Intentional denormalizations** (deliberately kept for RLS performance or external API semantics, either database-enforced or explicitly exempted).

| Table | Column(s) | Normal Form | Functional Dependency / Flaw | Status in Repo | Database Remedy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `idea_items` | `person_id` | **2NF** | `item_id -> person_id` (partial key dependency on composite key `(idea_id, item_id)`) | Fixed in `20261010040000` | Drop column; read via join with `items` |
| `document_chunks` | `kind`, `label`, `source_url`, `source_ref` | **3NF** | `document_id -> {kind, label, source_url, source_ref}` (transitive dependency on parent `documents`) | Fixed in `20261010040000` | Drop columns; join with `documents` in queries |
| `documents` | `is_public` | **3NF** | `label -> is_public` (transitive dependency: boolean was duplicate of `label = 'quotable'`) | Fixed in `20261010040000` | `generated always as (label = 'quotable') stored` |
| `drafts` | `tokens_in`, `tokens_out` | **3NF** | `tokens (jsonb) -> (tokens_in, tokens_out)` (hand-written derived values that drifted) | Fixed in `20261010040000` & `20261011120000` | `generated always as (...) stored` using safe parser |
| `people` | `first_touch_at`, `last_touch_at` | **3NF** / Derived | `touches -> min/max(occurred_at)` (hand-written read-then-write caches in app code) | Fixed in `20261010040000` | Maintained exclusively by trigger `touches_person_span` |
| `plans` | `allowed_models` | **1NF** | Array `text[]` searched with `= any` (1:N relationship disguised as a column) | Fixed in `20261010040000` | Extracted to relation table `plan_models(plan_id, model)` |
| `model_calls` | `tokens_in`, `tokens_out`, `cost_usd` | **3NF** | `usage (jsonb) -> (tokens_in, tokens_out, cost_usd)` (hand-written derived values) | **Current (Unfixed)** in `20261015010000` | Make generated columns or compute from `usage` |
| `model_calls` | `project_id` | **3NF** | `item_id -> project_id` (unconstrained parent copy without composite foreign key) | **Current (Unfixed)** in `20261015010000` | Add composite FK `(item_id, project_id) references items(id, project_id)` |
| `code_questions` | `cost_usd` | **3NF** / Derived | `usage (jsonb) -> cost_usd`, or aggregate `sum(model_calls.cost_usd)` written by app code | **Current (Unfixed)** in `20261015010000` | Make generated from `usage` or update via trigger |
| `code_questions` | `project_id` | **3NF** | `item_id -> project_id` (unconstrained parent copy without composite foreign key) | **Current (Unfixed)** in `20261015010000` | Add composite FK `(item_id, project_id) references items(id, project_id)` |
| `child tables` (`items`, `touches`, etc.) | `project_id` | **3NF** (Redundancy) | `parent_id -> project_id` (stored for RLS and index performance) | Enforced in `20261010040000` | Enforced via composite foreign keys on `(id, project_id)` |

---

## 2. Detailed Breakdown by Normal Form

### 2.1. Second Normal Form (2NF): "The Whole Key"

A table violates 2NF if it has a composite candidate key and any non-prime column depends on only a proper subset of that key.

#### `idea_items.person_id`
* **Schema Definition (`20261008230200_backend_v1.sql`):**
  ```sql
  create table idea_items (
    idea_id uuid not null references ideas(id) on delete cascade,
    item_id uuid not null references items(id) on delete cascade,
    person_id uuid not null references people(id) on delete cascade,
    project_id uuid not null references projects(id) on delete cascade,
    quote text,
    created_at timestamptz not null default now(),
    primary key (idea_id, item_id)
  );
  ```
* **The Violation:** The primary key is composite `(idea_id, item_id)`. However, `person_id` is already a property of the item (`items.person_id`). Thus, the functional dependency is:
  $$\text{item\_id} \rightarrow \text{person\_id}$$
  `person_id` depends solely on `item_id`, violating 2NF ("the whole key").
* **Consequences:** The counter `ideas.asked_by` ("how many distinct people asked for this idea") read from this redundant copy. If an item was reassigned to another person (e.g., merging duplicates), `idea_items.person_id` could disagree with `items.person_id`.
* **Resolution (`20261010040000_normal_forms.sql`):**
  - Dropped `idea_items.person_id`.
  - Recount triggers (`ideas_recount`, `items_person_recount`) and views (`inbox_by_person`) now join `idea_items` with `items` to resolve `items.person_id`.

---

### 2.2. Third Normal Form (3NF): "Nothing but the Key"

A table violates 3NF if a non-key column is functionally determined by another non-key column (transitive dependency $X \rightarrow Y \rightarrow Z$), or if redundant parent copies can drift because the database does not enforce consistency.

#### A. `document_chunks` Parent Attribute Copies
* **Schema Definition (`20261008230100_knowledge_chunks.sql`):**
  ```sql
  create table document_chunks (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references projects(id) on delete cascade,
    document_id uuid not null references documents(id) on delete cascade,
    ord int not null,
    kind text not null check (...),
    title text not null,
    source_url text,
    source_ref text,
    label text not null default 'quotable',
    ...
  );
  ```
* **The Violation:** A chunk belongs to a document (`document_id`). The document already has `kind`, `label`, `url`, and `source_ref`. Storing `kind`, `label`, `source_url`, and `source_ref` on every chunk created a transitive dependency:
  $$\text{chunk\_id} \rightarrow \text{document\_id} \rightarrow \{\text{kind}, \text{label}, \text{url}, \text{source\_ref}\}$$
* **Resolution (`20261010040000_normal_forms.sql`):**
  - Dropped `kind`, `source_url`, `source_ref`, and `label` from `document_chunks`.
  - Updated vector retrieval RPC `match_document_chunks` to `JOIN documents d ON d.id = c.document_id`.

#### B. `documents.is_public` Duplicate Boolean
* **Schema Definition (`20261008230100_knowledge_chunks.sql` & `20261010010000_sources_voice_knowledge.sql`):**
  Both `is_public boolean` and `label text check (label in ('quotable', 'background'))` were stored on `documents`.
* **The Violation:** `is_public` was identically defined as `label = 'quotable'`:
  $$\text{label} \rightarrow \text{is\_public}$$
  Storing both allowed them to disagree (e.g., `is_public = true` with `label = 'background'`).
* **Resolution (`20261010040000_normal_forms.sql`):**
  - Dropped plain column `is_public`.
  - Added stored generated column: `is_public boolean generated always as (label = 'quotable') stored`.

#### C. `drafts.tokens_in` and `drafts.tokens_out` Hand-Written Derived Values
* **Schema Definition (`20261008170000_init.sql` & `20261009190000_draft_model_settings.sql`):**
  `drafts` stored `tokens jsonb` (the breakdown `{input, output, cache_read, cache_write, cost_usd}`), alongside plain integer columns `tokens_in` and `tokens_out`.
* **The Violation:** The totals are strict mathematical functions of the `tokens` JSON structure:
  $$\text{tokens} \rightarrow \text{tokens\_in} = \text{input} + \text{cache\_read} + \text{cache\_write}$$
  $$\text{tokens} \rightarrow \text{tokens\_out} = \text{output}$$
  Because application code wrote both independently, live rows diverged when providers omitted cache keys or used different total definitions.
* **Resolution (`20261010040000_normal_forms.sql` & `20261011120000_tokens_generated_safe.sql`):**
  - Replaced plain columns with stored generated columns using `hb_json_int(...)`.

#### D. `people.first_touch_at` and `people.last_touch_at` Hand-Written Cached Extrema
* **Schema Definition (`20261008170000_init.sql` & `20261008230200_backend_v1.sql`):**
  `people` stored `first_touch_at` and `last_touch_at` as plain timestamps.
* **The Violation:** The timestamps are aggregate functions of child rows:
  $$\text{touches for person\_id} \rightarrow \min(\text{occurred\_at}), \max(\text{occurred\_at})$$
  Because updates were performed in application code via read-then-write, concurrent touches caused race conditions, and certain write paths (such as GitHub issue touches) failed to update them.
* **Resolution (`20261010040000_normal_forms.sql`):**
  - Installed trigger `touches_person_span` on `touches` (`AFTER INSERT OR DELETE OR UPDATE OF person_id, occurred_at`), making Postgres the sole updater. Removed manual touch updates from `record_draft_outcome`.

---

### 2.3. Current / Reintroduced 3NF Violations in Latest Migrations

Migration `20261015010000_ask_code_model_calls.sql` introduced two new tables (`model_calls` and `code_questions`) that recreate unnormalized patterns:

#### A. `model_calls`: Hand-Written Derived Columns (`tokens_in`, `tokens_out`, `cost_usd`)
* **Schema Definition (`20261015010000_ask_code_model_calls.sql`):**
  ```sql
  create table model_calls (
    id bigint generated always as identity primary key,
    ...
    tokens_in int,               -- all prompt tokens (uncached + cache reads + cache writes)
    tokens_out int,
    usage jsonb,                 -- {input, output, cache_read, cache_write, cost_usd}
    cost_usd numeric(12, 6),     -- list price (pricing.ts); null: unknown or free (Gemini free key)
    ...
  );
  ```
* **The Violation:**
  Just as with `drafts`, `tokens_in`, `tokens_out`, and `cost_usd` are functional duplicates of fields inside `usage`:
  - In `supabase/functions/_shared/server/ask_code.ts` (lines 88–93):
    ```ts
    tokens_in: s.input + s.cache_read + s.cache_write,
    tokens_out: s.output,
    usage: { input: s.input, output: s.output, cache_read: s.cache_read, cache_write: s.cache_write, cost_usd: s.cost_usd },
    cost_usd: s.cost_usd,
    ```
  - In `supabase/functions/_shared/server/models.ts` (lines 46–50):
    ```ts
    tokens_in: r.tokens_in, tokens_out: r.tokens_out,
    usage: r.usage, cost_usd: r.usage?.cost_usd ?? null,
    ```
  These are plain columns written manually by the application layer. The database does not enforce consistency via generated expressions or triggers, reintroducing the exact 3NF drift issue previously solved in `drafts`.

#### B. `model_calls` and `code_questions`: Unconstrained `project_id` / `item_id`
* **Schema Definition (`20261015010000_ask_code_model_calls.sql`):**
  - In `model_calls`:
    ```sql
    project_id uuid references projects(id) on delete set null,
    item_id uuid references items(id) on delete set null,
    ```
  - In `code_questions`:
    ```sql
    project_id uuid not null references projects(id) on delete cascade,
    item_id uuid references items(id) on delete set null,
    ```
* **The Violation:**
  In table `items`, migration `20261010040000_normal_forms.sql` added:
  ```sql
  alter table items add constraint items_id_project unique (id, project_id);
  ```
  Every item functionally determines its project: $\text{item\_id} \rightarrow \text{project\_id}$.
  All existing child tables (`touches`, `idea_items`, etc.) use composite foreign keys:
  ```sql
  foreign key (item_id, project_id) references items (id, project_id)
  ```
  In `model_calls` and `code_questions`, `item_id` and `project_id` have independent foreign keys. A row can be inserted with `item_id` belonging to Project A and `project_id` set to Project B. The database does not maintain consistency.

#### C. `code_questions.cost_usd` Hand-Written Derived Value
* **Schema Definition (`20261015010000_ask_code_model_calls.sql`):**
  `code_questions` contains both `cost_usd numeric(12, 6)` and `usage jsonb` (which also contains `cost_usd`).
* **The Violation:**
  In `supabase/functions/_shared/server/ask_code.ts`:
  - On successful run: `cost_usd: run.usage.cost_usd`.
  - On failure (lines 104–106):
    ```ts
    const { data: steps } = await db.from("model_calls").select("cost_usd").eq("run_id", id);
    const spent = (steps ?? []).reduce((a, r) => a + Number(r.cost_usd ?? 0), 0);
    await db.from("code_questions").update({ status: "failed", error: msg.slice(0, 300), cost_usd: spent }).eq("id", id);
    ```
  The cost is an aggregate across child `model_calls` rows where `run_id = code_questions.id`. Writing it from application code creates a transitive dependency without database enforcement.

---

### 2.4. First Normal Form (1NF): Relations in Disguise

#### `plans.allowed_models`
* **Schema Definition (`20261009200000_plans_user_model.sql`):**
  ```sql
  create table plans (
    id text primary key,
    name text not null,
    default_model text not null,
    allowed_models text[] not null,
    ...
  );
  ```
* **The Violation:** `allowed_models` was a Postgres array `text[]` searched with `= any (allowed_models)` across `check_founder_draft_model`, `my_draft_model`, and `set_draft_model`. An array representing an entity relationship (a plan has many allowed models) violates 1NF atomicity.
* **Resolution (`20261010040000_normal_forms.sql`):**
  - Created junction table `plan_models(plan_id, model, ord)` with primary key `(plan_id, model)` and foreign key to `plans(id)`.
  - Added deferred foreign key constraint `plans (id, default_model) references plan_models (plan_id, model)`.
  - Dropped `plans.allowed_models`.

---

## 3. Deliberate Denormalizations and Controlled Exceptions

The schema retains specific denormalizations with explicit justifications documented in `20261010040000_normal_forms.sql`:

1. **`project_id` on Child Tables (`items`, `touches`, `document_chunks`, `idea_items`, `identities`, `documents`, `project_memory`):**
   - **Reason:** Supabase Row-Level Security (RLS) policies evaluate every query against `is_member(project_id)`. Storing `project_id` on children prevents expensive recursive joins.
   - **3NF Safeguard:** Every child table references the parent table using a composite foreign key on `(id, project_id) references parent(id, project_id)`. Drift is mathematically prevented by the engine.
2. **`ideas.asked_by` (Cached Count):**
   - **Reason:** Avoids `count(distinct person_id)` table scans during frequent inbox and idea queries.
   - **3NF Safeguard:** Database triggers (`ideas_recount` on `idea_items` and `items_person_recount` on `items`) are the exclusive writers.
3. **`ideas.github_issue_url`:**
   - **Reason:** Stores either the resolved GitHub issue URL or a pre-filled `github.com/<repo>/issues/new?title=...` link; not deterministically derivable from `github_issue_repo` + `github_issue_number`.
4. **`source_syncs.source`:**
   - **Reason:** Compound strings like `'devto:writing:<handle>'` and `'github:<repo>'` serve as opaque keys consumed directly by connector interfaces.
5. **`voice_samples.text_sha256`:**
   - **Reason:** Computed using JavaScript client/runtime whitespace normalization rules prior to ingestion, rather than database SQL normalization.
6. **Cached External API State (`projects.github_board_title`, `ideas.github_issue_state`, `ideas.github_board_status`):**
   - **Reason:** Read-only snapshots of external GitHub Projects and Issues state updated by periodic sweeps (`github-results`).

---

## 4. Recommended Fixes for Current Schema

To bring the current schema (`20261015010000_ask_code_model_calls.sql`) into full 3NF compliance, apply the following migrations:

```sql
-- 1. Enforce composite foreign keys on item_id + project_id
alter table model_calls
  drop constraint if exists model_calls_item_id_fkey,
  add constraint model_calls_item_fkey foreign key (item_id, project_id)
    references items (id, project_id) on delete set null;

alter table code_questions
  drop constraint if exists code_questions_item_id_fkey,
  add constraint code_questions_item_fkey foreign key (item_id, project_id)
    references items (id, project_id) on delete set null;

-- 2. Make model_calls token totals and cost generated columns
alter table model_calls
  drop column tokens_in,
  drop column tokens_out,
  drop column cost_usd;

alter table model_calls
  add column tokens_in int generated always as (
    case when coalesce(hb_json_int(usage->>'input'), hb_json_int(usage->>'cache_read'), hb_json_int(usage->>'cache_write')) is null then null
         else coalesce(hb_json_int(usage->>'input'), 0) + coalesce(hb_json_int(usage->>'cache_read'), 0) + coalesce(hb_json_int(usage->>'cache_write'), 0) end
  ) stored,
  add column tokens_out int generated always as (hb_json_int(usage->>'output')) stored,
  add column cost_usd numeric(12, 6) generated always as (nullif(usage->>'cost_usd', '')::numeric(12, 6)) stored;
```
