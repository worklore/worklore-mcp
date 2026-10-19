# What in the schema isn't in 3NF

The audit uses Kent's test: every non-key column must be a fact about **the key** (1NF), **the whole key** (2NF), and **nothing but the key** (3NF). It covers the schema as it stands after all 26 migrations, and it checks the server code in `supabase/functions` to see who writes each column.

**Context.** `20261010040000_normal_forms.sql` already fixed the problems the guide describes:

- `idea_items.person_id` was dropped.
- `document_chunks` no longer stores copies of `kind`, `label`, `source_url` or `source_ref`.
- `documents.is_public` and `drafts.tokens_in` / `tokens_out` are now generated columns.
- `people.first_touch_at` / `last_touch_at` are kept by a trigger.
- `plans.allowed_models` became the `plan_models` table.
- The `project_id` copies are checked by composite foreign keys.

Those are fine now and not repeated below. What follows is what's **still** not in 3NF. Most of it came in after that migration or was missed by it.

> I had no database access, so I haven't counted would-be violations on live data. Each finding comes with a read-only query for that count. Run it before writing any migration (guide step 4).

---

## A. Derived values written by hand (the `drafts.tokens_*` problem, back again)

### A1. `model_calls.tokens_in`, `tokens_out`, `cost_usd` are copies of `model_calls.usage`
`20261015010000_ask_code_model_calls.sql:28-31`

- `tokens_in` is `usage.input + usage.cache_read + usage.cache_write`, and the column comment says so.
- `tokens_out` is `usage.output`.
- `cost_usd` is `usage.cost_usd`.

All three are non-key columns determined by another non-key column, so they break 3NF. They're written separately in app code (`_shared/askcode` → `ask_code.ts:89-91`, `usage.ts:modelCallRow`), so nothing makes them agree. This is exactly what `drafts` fixed two migrations earlier.

**Move:** generated columns using the same `hb_json_int` expression as `drafts.tokens_in` (`20261011120000_tokens_generated_safe.sql`). `cost_usd` could be `nullif(usage->>'cost_usd','')::numeric` or a lenient helper. After that, `modelCallRow` stops sending these fields.

```sql
select count(*) from model_calls where
  tokens_out is distinct from hb_json_int(usage->>'output')
  or cost_usd is distinct from nullif(usage->>'cost_usd','')::numeric
  or tokens_in is distinct from (case when coalesce(hb_json_int(usage->>'input'),hb_json_int(usage->>'cache_read'),hb_json_int(usage->>'cache_write')) is null then null
       else coalesce(hb_json_int(usage->>'input'),0)+coalesce(hb_json_int(usage->>'cache_read'),0)+coalesce(hb_json_int(usage->>'cache_write'),0) end);
```

### A2. `code_questions.cost_usd` and `usage` duplicate each other, and both duplicate `model_calls`
`20261015010000_ask_code_model_calls.sql:72-74`

- `cost_usd` is `usage.cost_usd`: a non-key column determined by another non-key column (3NF).
- `usage` (the run totals) and `steps` are also aggregates of the `model_calls` rows where `run_id = code_questions.id`.
- The two code paths disagree. On success, `cost_usd` comes from the agent's in-memory total (`ask_code.ts:96`). On failure, the code re-sums `model_calls` (`ask_code.ts:104-106`).
- `model_calls` inserts are best-effort ("a failed insert is a console line"), so the sum can come out lower than the stored total.

**Move:** at minimum, make `cost_usd` a generated column from `usage`. Ideally, decide which source is authoritative: either this row, or `model_calls` read through a view (`sum(...) group by run_id`).

### A3. `voice_samples.quality` is a copy of `voice_samples.scores->'quality'`
`20261010010000_sources_voice_knowledge.sql:25-26`

`voice.ts:96-100` builds `scores = { …, quality, … }` and returns the same `quality` next to it. `run.ts:136` writes both. One exception: rule rejections write `quality: 0, scores: null`, so for those rows the two already say different things.

**Move:** `quality real generated always as ((scores->>'quality')::real) stored`. Rule rejections would then get a NULL quality, which is more honest anyway. Alternatively, drop `quality` from the JSON.

```sql
select count(*) from voice_samples where quality is distinct from (scores->>'quality')::real;
```

### A4. `drafts.posted_by` / `posted_at` are functions of `outcome`, `decided_by`, `decided_at`
`20261008170000_init.sql:184`, `20261008230200_backend_v1.sql:68`

The only writer is `record_draft_outcome`. It sets:

- `posted_by = uid` and `decided_by = uid`
- `posted_at = now()` and `decided_at = now()` (the same timestamp in one transaction)

It does this only when the outcome is a "posted" one, and otherwise leaves them null. So `posted_by = case when outcome in ('posted_as_is','posted_edited') then decided_by end` holds, and the same goes for `posted_at`. That's a transitive dependency. Readers already treat them as interchangeable (`coalesce(posted_by, decided_by)` in `hb_voice_from_draft` and in `run.ts:108`).

**Move:** drop `posted_by` / `posted_at`, or make them generated columns, since the expression only reads the same row. Keep them only if a future "posted by someone other than the decider" flow is planned, and if so, write that down.

```sql
select count(*) from drafts where
  posted_by is distinct from case when outcome in ('posted_as_is','posted_edited') then decided_by end
  or posted_at is distinct from case when outcome in ('posted_as_is','posted_edited') then decided_at end;
```

---

## B. 3NF: columns that are facts about a *parent*, not about this row's key

### B1. `touches.platform` (and, for incoming touches, `kind`, `occurred_at`, `url`, `text`) copy the item
`20261008170000_init.sql:199-203`

- `item_id → platform` holds for every touch of an item. `record_draft_outcome` writes `it.platform`, and `insertItem` writes `row.platform`.
- The composite foreign key `(item_id, project_id, person_id)` doesn't include `platform`, so nothing stops it from disagreeing with the item.
- For `direction = 'in'`, `store.ts:89-92` also copies the item's `kind`, `posted_at`, `url` and `text` into the touch, so every incoming comment's text is stored twice.

**Move:**

- For `platform`: extend the FK to `(item_id, project_id, person_id, platform)` → `items (id, project_id, person_id, platform)`, which needs a matching unique constraint on items. That's the same pattern as `items_account_fkey`.
- For the incoming copies: read them through the item (`coalesce(t.text, i.text)`), or have the touch store only the item reference when `item_id` is set.
- Touches without an item (imports, email, outreach) keep their own columns.

```sql
select count(*) from touches t join items i on i.id = t.item_id where t.platform <> i.platform;
select count(*) from touches t join items i on i.id = t.item_id
 where t.direction = 'in' and (t.text is distinct from i.text or t.url is distinct from i.url or t.occurred_at <> i.posted_at);
```

### B2. `ideas.quote` is a copy of the first `idea_items.quote`
`20261008230200_backend_v1.sql:79`

The comment calls it "the exact phrase heard (first ask)". `ideas.ts:58-67` computes one `quote` and writes it to both `ideas` and `idea_items`.

**Move:** drop it and read the first ask: `select quote from idea_items where idea_id = … order by created_at limit 1`, as a view or a lateral join. If the founder is meant to edit the idea's quote separately, then it's a separate fact. Rename it and say so.

```sql
select count(*) from ideas d where d.quote is distinct from
  (select ii.quote from idea_items ii where ii.idea_id = d.id order by ii.created_at limit 1);
```

### B3. `document_chunks.title` contains `documents.title`; `published_at` / `published_precision` copy the document
`20261008230100_knowledge_chunks.sql:36,41`

- **`title` (1NF and 3NF).** It holds `"Doc title › Section"` (`chunk.ts:76`). The document-title part is a copy of `documents.title`, and the value is two facts in one string. `chunk.ts:96` even splits it back apart on `" › "`.
  - **Move:** store `heading` only, and build the display title in `match_document_chunks` from `d.title` and `c.heading`.
- **`published_at` / `published_precision`.** The schema says these are per chunk ("as new as its newest line"), and `normal_forms.sql` kept them for that reason. But the only writer, `knowledge.ts:104-105`, writes the document's own `published` / `day` into every chunk. Line-level dating isn't implemented, so today they're pure copies.
  - **Move:** either implement per-chunk dating, or drop the columns and read `d.published_at`. If per-chunk dating is planned soon, add a `check` or document it, so the copy is a conscious choice.

```sql
select count(*) from document_chunks c join documents d on d.id = c.document_id
 where c.published_at <> d.published_at or c.published_precision <> d.published_precision;
select count(*) from document_chunks c join documents d on d.id = c.document_id
 where d.title is not null and c.title <> d.title and c.title not like d.title || ' › %';
```

### B4. `projects.github_board_id` / `github_board_title` depend on `(github_board_owner, github_board_number)`
`20261014010000_github_board_results.sql:20-21`

The migration says it outright: "owner + number is the board's address … id is its GraphQL node id; title is GitHub's, cached". So `owner, number → id, title` is a transitive dependency inside `projects`. If two projects link the same board, the title is cached twice and can drift.

**Move:** either a `github_boards (id pk, owner, number, title, unique (owner, number))` table referenced by `projects.github_board_id`, or accept it as a cache of GitHub and refresh it in one place. The `projects_github_board_whole` check only makes the four columns null together. It doesn't make them consistent with each other.

### B5. `items.my_post` depends on the post the item is under, not on the item
`20261008170000_init.sql:154`

`my_post` is the `{url, title, text}` snapshot of the project's article. Every comment under the same article repeats it, so it's determined by `root_ref` (non-key → non-key), and `richerContext` (`store.ts:103-110`) updates it one item at a time. The same goes in part for `thread`: siblings share the part of the thread above them.

**Move:** a `posts` table (project_id, platform, external_id → url, title, text) with `items.post_id`. Or, if per-item snapshots are deliberate ("what the founder saw when answering"), keep it and document it under "kept on purpose".

### B6. `voice_samples` rows with `source = 'hearback'` are copies of a draft, with the foreign key hidden in a string
`20261010010000_sources_voice_knowledge.sql:15-20`

`hb_voice_from_draft` builds these columns from the draft and its item:

| `voice_samples` column | copied from |
|---|---|
| `external_id` | `'draft:' \|\| drafts.id` (a foreign key hidden inside a string, a 1NF smell) |
| `text` | `drafts.final_text` |
| `source_url` | `drafts.posted_url` |
| `posted_at` | `drafts.posted_at` |
| `founder_id` | `posted_by` / `decided_by` |
| `platform` | `items.platform` |
| `project_id` | `items.project_id` |
| `context` | `left(items.text, 600)` |

Nothing links the sample back to the draft, so deleting or editing the draft leaves the sample out of sync.

**Move:** add a real `draft_id uuid references drafts(id) on delete cascade` (unique). For samples from other sources (`own_writing`, `github`), these columns are original facts and stay.

### B7. Cross-project global facts on `identities` (2NF against the candidate key `(project_id, platform, handle)`)
`20261008170000_init.sql:133-134`

`external_id` (e.g. a Bluesky DID), `profile_url` and `public_profile` are facts about the account `(platform, handle)`, not about the project. So they depend on only part of the candidate key, which breaks 2NF. Someone who comments in two projects has their profile fetched and stored twice. `accounts.external_id` (same key shape) and the platform columns of `items` (`url`, `text`, `posted_at` against `(project_id, platform, external_id)`) are the same pattern.

**Recommendation: keep it on purpose.** These are per-tenant snapshots, and splitting them out would mean global rows that RLS can't scope by `project_id`. Record it in the "left as is" list in the migrations so it's a decision, not an accident.

---

## C. Smaller items

- **`people.avatar_url`** is overwritten from the latest fetched identity whenever it differs (`store.ts:38`). So it's a cache of an identity's profile. If a person has two identities, it flips between them. `display_name` only fills blanks, so it's a founder-owned fact and that's fine.
- **`ideas.github_issue_state` vs `github_issue_state_reason` / `github_issue_closed_at`.** `state_reason` (completed / not_planned / duplicate → closed; reopened → open) partly determines `state`. This is a cached GitHub snapshot written in one place (`github_results.ts`), so it's low risk. A check such as `(github_issue_state = 'closed') = (github_issue_closed_at is not null)` would keep it honest.
- **`projects.settings->'draft_model'`** is dead data: the migration comment says the server no longer reads it. It isn't a normal-form problem, but it's a second, stale home for "which model drafts".
- **`item_themes`** has no `project_id`, so nothing stops linking an item to another project's theme. This isn't redundancy. It's the same cross-project hole that `normal_forms.sql` closed for `documents` and `project_memory`.

---

## Already kept on purpose (checked, not findings)

These are listed in `normal_forms.sql` and are still enforced or justified:

- the `project_id` copies, which composite foreign keys check
- `ideas.asked_by`, kept by triggers
- `ideas.github_issue_url`
- the opaque `source_syncs.source`
- `voice_samples.text_sha256` (it uses JavaScript's whitespace rule)
- `themes.position` vs `project_memory`

`items.triage_*`, `projects.url_key`, `documents.is_public` and `drafts.tokens_*` are generated columns, so they're fine.

## Suggested order

1. **A1–A3:** generated columns. Mechanical, the guard is easy, and it repeats the existing `drafts.tokens` pattern.
2. **B1** (`touches.platform` FK) and **B2** (`ideas.quote`).
3. **A4 and B3:** decide whether a planned feature (a different poster, per-chunk dating) justifies the column. If not, drop it.
4. **B4–B7:** design decisions. Either normalize, or write them into the "left on purpose" list.

For each one, follow the guide's steps 4–7: count on production with the queries above, add a `do $$ … raise exception … $$` guard in the migration, test on `supabase start`, update the writers (an insert that sets a generated column fails), then deploy together with the code.
