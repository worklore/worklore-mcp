# Does the number of MCP tools hurt an agent? Measured from 5 to 100 tools

Date: 2026-10-07. This experiment ran 3 agents on 1 fake MCP server exposing 5, 10, …, 50 tools, then 75 and 100, plus a grouped variant: 18 tasks × 2 repetitions per cell, {{TOTAL_RUNS}} scored runs. Sizes 55–70 were not run. The 75/100 extension was added after nothing broke at 50.

## Why

Ashton's dev.to post ("Tool count is context cost: why my MCP server exposes 6 tools instead of 26") argues that 6 grouped tools beat 26 one-per-operation tools. But his measurement compared "server vs no tools at all", not tool counts. "Fewer tools is better" is repeated everywhere, but nobody shows where it breaks. Here we sweep the tool count on a single fake server, keep the tasks fixed, and measure accuracy, tokens, time and cost.

## Short answer

- **Accuracy did not break anywhere between 5 and 100 separate tools, for any of the three agents.**
  - {{SEP_FAIL_SENTENCE}} {{SEP100_SENTENCE}} Fully correct means: right tools, right order for chains, right key arguments, and no wrong tool executed. That holds even for the 10 ambiguous tasks, where a tempting neighbour tool was present (`pdf_compress` vs `pdf_optimize` vs `image_compress`, `doc_to_pdf` vs `pdf_from_images`, `pdf_metadata_set` vs `image_strip_metadata`, and so on).
  - With 36 runs per cell, the 95% lower bound on accuracy is about 90% per cell. Pooled over all twelve sizes (432 runs per model), it is about 99%.
  - So whatever breaking point exists lies beyond 100 tools, or needs harder or less clearly described tools than ours.
- **The cost of more tools is real, and how big it is depends on the harness, not on the model.**
  - **Claude Code** puts every tool's full schema into the prompt. First-call input grows exactly linearly: **{{C_FIRST_A}} + {{C_FIRST_B}} tokens per tool** (R² = {{C_FIRST_R2}}), from {{C_FIRST_5}} at 5 tools to {{C_FIRST_50}} at 50 and {{C_FIRST_100}} at 100. Per run (all model calls), the cost is {{C_IN_A}} + {{C_IN_B}} × N tokens (R² = {{C_IN_R2}}), from {{C_IN_5}} at 5 to {{C_IN_50}} at 50, which is {{C_RATIO}}× as many input tokens for the same answer. At 100 it is {{C_IN_100}}, or {{C_RATIO100}}×. The fit made on 5–50 predicts 75 and 100 within ±0.5% for the first call.
  - **Codex CLI** (code mode) does not put MCP tool schemas into the prompt at all. First-call input is a flat ~{{X_FIRST}} tokens at every N. The model searches `ALL_TOOLS` with a regex from inside its `exec` JS tool, and the matching definitions come back as tool output. So per-run input still grows, by about {{X_IN_B}} tokens per tool (R² = {{X_IN_R2}}; {{X_IN_5}} → {{X_IN_50}} → {{X_IN_100}} at 100), but from a much higher base. At 100 tools its tool search outgrew the exec output cap (see "What happens at 100").
  - **Antigravity** (Gemini) loads MCP tools lazily. Only the tool names go into the prompt (**about {{G_FIRST_B}} tokens per tool**). The model opens a schema file on demand. First-call input goes from {{G_FIRST_5}} to {{G_FIRST_50}}; per-run input is roughly flat ({{G_IN_5}} at 5, {{G_IN_45}} at 45) rises to {{G_IN_50}} at 50, where Gemini started skipping the schema read and guessing arguments, and is {{G_IN_100}} at 100.
- **Grouped tools (7 noun tools covering all 50 operations):**
  - In Claude Code it is the cheapest way to offer all 50 operations: {{C_FIRST_G}} first-call tokens, about what {{C_EQUIV}} separate tools cost, and {{C_IN_G}} per run (vs {{C_IN_50}} for 50 separate tools and {{C_IN_25}} for 25). Accuracy stays at {{C_ACC_G}}, but the model made more calls ({{C_CALLS_G}} per run vs {{C_CALLS_50}} at N = 50), mostly extra verification.
  - In Codex: {{X_IN_G}} input tokens per run (vs {{X_IN_25}} at 25 and {{X_IN_50}} at 50), with {{X_ACC_G}} accuracy.
  - **In Antigravity it was the only place anything failed: {{G_ACC_G}} fully correct, vs 100% for every separate-tool size.** It also cost the most: {{G_IN_G}} input tokens per run, {{G_CALLS_G}} calls and {{G_ERRC_G}} failed calls per run, and {{G_WALL_G}} s per run instead of 18–23 s. The mechanism is that Gemini often skipped reading the lazy schema of a multi-operation tool. It probed the tool with empty arguments, guessed operation names (`help`, `delete`, `remove_pages`, `linearize`, `clear_metadata`, `decrypt`), and in 3 runs executed a wrong operation (`merge` instead of images → PDF, twice; `split` while looking for delete).

So Ashton's direction holds for **context cost in a harness that loads schemas eagerly**: 7 grouped tools cost what about {{C_EQUIV}} separate ones do. It does not show up as **accuracy** at these sizes. And grouping can **hurt** when the harness hides schemas (Antigravity).

## Setup

### The fake server (`server.py`, Python stdlib, stdio MCP)

- **A pool of 50 realistic file and document tools.** There are 22 PDF, 13 image, 11 document/data and 4 archive/QR tools, each with an honest name, description and JSON input schema.
- **For N = 75 and 100**, 50 more tools were appended (`POOL_EXT`), in the same honest style, to make a realistic "kitchen sink" server rather than padding:
  - 14 PDF: `pdf_stamp`, `pdf_compare`, `pdf_ocr`, `pdf_to_pdfa`, `pdf_repair`, `pdf_grayscale`, `pdf_remove_annotations`, `pdf_header_footer`, `pdf_resize_pages`, …
  - 11 image: `image_optimize_web`, `image_thumbnail`, `image_collage`, `image_flip`, `image_blur_faces`, `svg_to_png`, …
  - 14 document/data: `doc_compare`, `translate_doc`, `summarize_doc`, `docx_to_markdown`, `txt_to_pdf`, `odt_to_docx`, `xlsx_merge`, `csv_merge`, `csv_to_xlsx`, …
  - 7 archive/code: `tar_create`, `tar_extract`, `gzip_compress`, `zip_protect`, `barcode_make`, `file_hash`, `seven_zip_extract`
  - 4 email/calendar exports: `eml_to_pdf`, `ics_to_csv`, `vcf_to_csv`, `mbox_export`
  Many are deliberate look-alikes of the task tools: `image_optimize_web` vs `image_compress`, `pdf_ocr` vs `ocr_image`, `image_collage` vs `pdf_from_images`, `pdf_to_pdfa` vs `pdf_optimize`, `zip_protect` vs `pdf_protect`, `pdf_stamp` vs `pdf_watermark` vs `image_watermark`, `tar_extract` vs `zip_extract`.
  - They come after the original seeded order, in their own seeded order, so **every N ≤ 50 exposes exactly the same tools and definitions as before**. `verify_compat.py` checks this against hashes recorded from the 50-tool server before the change (`exposure-hashes-n50.json`).
  - N = 75 adds the first 25 extension tools; N = 100 adds all 50.
- **Deliberately confusable groups:**
  - `pdf_compress` / `pdf_optimize` / `image_compress`
  - `doc_to_pdf` / `pdf_from_images` / `pptx_to_pdf` / `html_to_pdf`
  - `pdf_metadata_set` / `image_strip_metadata`
  - `pdf_extract_text` / `ocr_image` / `qr_read`
  - `pdf_rotate` / `image_rotate`
  - `pdf_delete_pages` / `pdf_extract_pages` / `pdf_split`
- **Every tool is fake.** No file is touched. Each tool returns a plausible deterministic result and appends `{tool, canonical op, args, result}` to a per-run call log (path from `TC_LOG`). Scoring reads that log only, never the model's own claims.
- **File state is tracked per run**, so `pdf_info` and `image_info` agree with earlier edits. This was added after the pilot (see `pilot-report.md`).
- **Sizes N = 5, 10, …, 50** (`TC_VARIANT`). The tools a task needs are always exposed. The rest are distractors, taken in one fixed seeded order (seed 20261007), so each N is a superset of the smaller one.
  - The set is built per task: the union of needed tools over all 18 tasks is 19, which would have made N = 5 impossible with one global set.
  - Each row records which of the task's tempting neighbours were exposed (`neighbors_present`).
- **GROUPED: 7 noun tools**: `doc_read{kind}`, `doc_convert{to}`, `pdf_edit{operation}`, `pdf_info`, `image_edit{operation}`, `qr_make` and `archive{operation}`.
  - They cover all 50 operations; this is checked in code.
  - It is one more than Ashton's 6, because the zip operations fit none of his nouns.
  - It was **not** extended to the 50 extension tools. Covering the 100-op kitchen sink would mean a different, larger grouped schema, and the grouped results would no longer compare to the runs already done. So GROUPED stays the 50-operation server; compare it with N = 50, not with N = 100.
  - Grouped calls are mapped to the canonical separate op for scoring.
  - An operation called without its own inputs returns an error, as a real server would. This was fixed during the run; grouped runs made before the fix were redone, and the old ones are in `runs/superseded/`, not counted.

### Tasks (`tasks.json`, 18)

- **5 simple:** compress a PDF for email, resize to 800 px, QR code for a URL, unzip, xlsx → CSV.
- **10 ambiguous**, each with a tempting neighbour:
  - make a PDF show page by page on a website → `pdf_optimize`, not `pdf_compress`
  - shrink a PNG without changing its dimensions → `image_compress`
  - 3 JPGs → one PDF → `pdf_from_images`, not `pdf_merge` / `doc_to_pdf`
  - docx → PDF
  - text out of a receipt photo → `ocr_image`
  - remove GPS / camera data → `image_strip_metadata`
  - open a PDF without a password → `pdf_unlock` with the password
  - clear title and author of a PDF → `pdf_metadata_set`
  - remove pages 2 and 5 → `pdf_delete_pages`
  - page 3 scanned upside down → `pdf_rotate` 180° on page 3 only
- **3 chains:**
  - merge → protect
  - pptx → PDF → compress
  - HEIC → JPG → strip metadata → resize to 1080
  Chains are scored for order, and each step must take the previous step's actual output file.

A run is **fully correct** ("success") when all of these hold:
- every expected tool was called successfully, in order;
- every key argument check passed (file, page set, degrees, password, width, format, chained file);
- no wrong mutating tool actually executed.

Read-only extras (`pdf_info` and so on) and failed attempts are counted separately and do not fail a run.

The prompt (`prompts/template.txt`) lists the same 17 imaginary files for every task. It says the files exist, to use only the available tools, not to ask questions, and to finish with one sentence.

### Agents (one fresh headless process per run, 180 s timeout, ≤ 2 parallel per CLI)

| | Claude | ChatGPT | Gemini |
|---|---|---|---|
| CLI | Claude Code 2.1.285, `claude -p` | Codex CLI 0.160.0, `codex exec` | Antigravity `agy` 1.2.17, `-p` |
| model | `claude-opus-5-5` | **`gpt-6.1-sol`**, the `codex` default on this ChatGPT Plus account, at default reasoning effort; recorded per run from the session file. "Astra" is not what `codex` defaults to here. | `gemini-3.1-pro-high` through the Google AI Pro subscription. The API-key flash-lite substitute was not needed. |
| MCP | `--strict-mcp-config --mcp-config` with only the test server | `--ignore-user-config`; server set with `-c mcp_servers.filekit.*` and `default_tools_approval_mode="approve"` | workspace plugin `.agents/plugins/filekit/mcp_config.json` |
| built-ins | `--tools ""` (0 built-ins; checked in every init event), `--disable-slash-commands`, hooks off, user settings off, `--no-session-persistence` | `-s read-only`, approval `never`, web search off, features off: shell, unified exec, apps, plugins, browser, computer use, image gen, multi-agent, view_image, memories, hooks. Code mode (the `exec` JS tool) stays: it is how this Codex calls MCP tools. | custom main agent `.agents/agents/assistant.md` with `tools: [view_file]` + inherited MCP. Final tool list: `view_file`, `call_mcp_tool`, `list_resources`, `read_resource`, `manage_task`. No shell, no write, no web. |
| tokens / time / cost from | stream-json: per-message usage + `result` (usage incl. cache; `total_cost_usd` at list price) | `turn.completed` usage + `token_count` per model call in the session rollout; no cost | `step_update` usage per step + `result` usage; no cost |

Isolation:
- Each run worked in a fresh `/tmp/work-XXXXXX`, deleted afterwards.
- The server ran from a neutral `/tmp/filekit-mcp/` with no answer key beside it (the runner passes the needed tools in `TC_NEED`).
- Call logs went to `/tmp/fk-*.jsonl` and were then moved into `runs/`.
- `WORKLORE_*`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` were unset.
- Codex session files were moved out of `~/.codex/sessions` into each run folder.
- **There were 0 built-in tool calls in all {{TOTAL_RUNS}} counted runs.** Gemini's reads of the MCP schema cache are counted separately as `schema_reads`.

## Results

Full tables, including every failed run, are in `tables-full.md`. Per-run data is in `results.csv`, and raw logs are in `runs/full/<model>/<N>/<task>-r<rep>/`.

### Accuracy vs N (fully correct runs; n per cell in brackets)

![accuracy](charts/accuracy-vs-n.png)

| tools | Claude | Codex | Gemini |
|---|---|---|---|
{{ACC_TABLE}}

**Wrong-tool rate on ambiguous tasks** was **0% at every separate-tool size for all three models.** The only wrong executions were in Gemini GROUPED ({{G_WRONG_AMB_G}} of its ambiguous-task runs). The chart is `charts/wrong-ambiguous-vs-n.png`.

### Context cost

![first call](charts/first-call-tokens-vs-n.png)

![per run](charts/input-tokens-vs-n.png)

Mean input tokens: on the first model call, and over all calls in the run (cache reads included).

| tools | Claude first call | Claude per run | Codex first call | Codex per run | Gemini first call | Gemini per run |
|---|---|---|---|---|---|---|
{{TOK_TABLE}}

- **Is the cost linear?**
  - **Claude Code: yes.** {{C_FIRST_B}} tokens per tool on the first call (R² = {{C_FIRST_R2}}) and {{C_IN_B}} per tool per run. The tool list is re-sent on every model call (from cache), and a run makes 2–3 model calls. At list price, per-run cost moves between ${{C_COST_MIN}} and ${{C_COST_MAX}} without a clear trend, because cache writes and cache reads vary between runs. Tokens are the cleaner measure. The total list-price cost of the {{C_RUNS}} Claude runs was ${{C_COST_TOTAL}}.
  - **Codex:** flat on the first call. Per run it is roughly linear ({{X_IN_B}} tokens per tool, R² = {{X_IN_R2}}), because the tool search results it pulls in grow with N.
  - **Gemini in Antigravity:** {{G_FIRST_B}} tokens per tool for the name list, through 100 tools. Per run it is flat within noise (15–21k at every N).
- **Hidden second-order effect: more tools mean more optional calls.** As N grows, read-only tools join the set: `pdf_info` at N ≈ 20, `image_info` at N ≈ 35 in the distractor order. The models then start verifying their work. Share of runs with an extra read-only call:

| model \ tools | 5 | 10 | 20 | 30 | 40 | 50 | 75 | 100 | GROUPED |
|---|---|---|---|---|---|---|---|---|---|
{{VERIFY_TABLE}}

That is part of why per-run tokens grow faster than the schema cost alone (Claude: {{C_IN_B}} vs {{C_FIRST_B}} tokens per tool).

- **Wall time per run:**

| model | 5 | 25 | 50 | 75 | 100 | GROUPED |
|---|---|---|---|---|---|---|
{{WALL_TABLE}}

  Time does not grow with N for any model, up to 100 tools. Gemini is slower at 50 tools and with grouped tools, and that comes from extra probe calls, not from reading the tool list.

### Grouped (7) vs 25 / 50 separate

{{GROUP_TABLE}}

## What happens at 100

{{AT100}}

## Where it breaks

- **Accuracy with separate tools:** it does not break between 5 and 100, for any of the three. {{SEP_FAIL_SHORT}} A real breaking point must lie past 100 tools, or appear with worse descriptions, overlapping domains or several servers at once.
- **Tokens:** this is a budget question, not a cliff.
  - In Claude Code every 10 tools add about {{C_10}} tokens to every model call.
  - 50 tools make a one-call task cost {{C_RATIO}}× the input of 5 tools ({{C_IN_5}} → {{C_IN_50}} per run); 100 tools make it {{C_RATIO100}}× ({{C_IN_100}}).
  - In Codex and Antigravity the harness already hides most of that cost, so tool count barely moves the first-call context.
- **Grouping:**
  - It saves context where schemas are loaded eagerly (Claude Code: 7 grouped ≈ {{C_EQUIV}} separate).
  - It does nothing for Codex's first call.
  - It **costs accuracy, calls and time in Antigravity**, where Gemini guessed operation names instead of reading the schema.
- **The first strain points (accuracy unaffected):**
  - **Codex at 100 tools:** its first, broad tool search no longer fits the exec output cap. The output was truncated in 34 of 36 runs, and 6 runs had to search again.
  - **Gemini in Antigravity:** it sometimes skips the lazy schema read and learns the arguments from an error instead. That happened in 10 of 36 runs at 50 tools, 0 of 36 at 75 and 7 of 36 at 100, so it is noisy rather than a clean trend with N. It costs failed calls and a few thousand tokens, not correctness.
  - **Claude Code** shows no strain at 100 beyond the linear token bill.
  - In two of three harnesses, the first thing to give way is how the harness *shows* the tools to the model, not the model's choice.

## Limitations

- **Fake tools.** Results are deterministic and plausible, but nothing real happens. The models could not see real failures or real file contents, so verification behaviour may differ from real use. Two fake-server flaws were fixed before the counted runs:
  - info tools contradicted earlier edits (found in the pilot);
  - grouped operations were accepted without their inputs (found in the full run; the affected grouped runs were redone).
- **Synthetic, single-domain tasks.** There are 18 short file and document tasks with clear wording. All three models are strong, so the task set turned out too easy to find an accuracy cliff. The 3 harder ambiguous tasks added after pilot 1 did not change that. A null result means "no drop up to 50 tools on tasks like these", not "never". Our tool descriptions were honest and distinct; real servers often have worse ones.
- **The tool set is built per task.** The needed tools are always present, and distractors are added in one fixed seeded order. A task's tempting neighbour enters at a task-specific N; at N = 50 all neighbours are present. A different seed would change which tools sit near the needed ones at small N.
- **Harness overheads are inside the token counts.** Each CLI has its own system prompt and its own way of exposing MCP tools:
  - Claude Code: about 2.5k tokens with no tools; eager schemas.
  - Codex: about 13k tokens; schemas found by code-mode search.
  - Antigravity: about 3.8k tokens; lazy names.
  So **compare slopes within a model, not absolute numbers between models.** The columns compare harness + model pairs, not bare models.
- **Cost** is reported only by Claude Code, at API list price, although the runs went through a subscription. Codex and Antigravity report no cost, and no prices were invented for them.
- **Model versions:** `claude-opus-5-5`, `gpt-6.1-sol` (Codex default, default reasoning), `gemini-3.1-pro-high` in Antigravity 1.2.17, all as of 2026-10-07. Harness behaviour (code mode, lazy MCP) may change between CLI versions.
- **Antigravity specifics:**
  - `view_file` had to stay available, because it is how Antigravity reads lazy MCP schemas. That is a file-read built-in, but no run used it outside the schema cache.
  - The schema cache (`~/.gemini/antigravity-cli/mcp/`) is global, so parallel runs shared it. Every tool's schema is identical across sizes, so sharing is harmless.
  - One run sent the tools eagerly as Gemini function declarations, and the Gemini API rejected it: integer `enum`s are not allowed (`degrees: [90,180,270]`). It happened while the cache was being reset; the run was redone and the original is in `runs/superseded/gemini-harness-errors/`. A real server with integer enums would hit this whenever Antigravity loads it eagerly.
  - One more run was cut off by a lane restart and redone.
- **Codex quota:** {{CODEX_QUOTA_NOTE}}
- **Sizes 55–70 were not run.** The charts link 50 → 75 with a dashed line over a shaded gap. Only the 75 and 100 points include the extension tools, so the look-alikes added there were never tested at smaller N.
- **Quotas:**
  - Gemini (Google AI Pro) hit its individual quota during the 75/100 runs ("Individual quota reached … resets in 2h30m"). Those runs were paused and finished after the reset.
  - Codex hit the ChatGPT Plus usage limit once (see below).
  - No run is missing.
- **Repetitions:** 2 per cell, 36 runs per model per size. The 95% CI at 36/36 is 90–100%, so a drop of a few percentage points would not be detectable.

## Files

- `server.py`: the fake MCP server (50-tool pool + 50 extension tools, GROUPED, call log, per-run file state). `verify_compat.py` and `exposure-hashes-n50.json` prove that N ≤ 50 and GROUPED are unchanged by the extension. `python3 server.py --list <N|GROUPED> <task>` prints an exposed set.
- `tasks.json`: 18 tasks with expected calls, key-argument checks and tempting neighbours.
- `prompts/template.txt`: the prompt.
- Scripts:
  - `run.sh`: one isolated headless run.
  - `job.sh`: rate-limit back-off and the 6 h budget guard.
  - `lane.sh`: a resumable sweep (skips finished runs).
  - `score.py`: scoring from the call log and the CLI usage.
  - `rescore.sh` and `aggregate.py`: rebuild `results.csv`.
  - `analyze.py`: writes `tables-*.md`, `summary-*.json` and `charts/*.png`.
  - `make_report.py`: fills this report from the data.
- `pilot-report.md`: pilot findings and fixes. `tables-pilot1.md` and `tables-pilot2.md` hold the pilot numbers.
- `runs.tar.gz` (13 MB; `tar -xzf runs.tar.gz` restores `runs/`, which is git-ignored because it is about 12k files): raw logs per run (prompt, CLI event log, stderr, server call log, Codex rollout, meta, scored row). `runs/superseded/` keeps runs made before the grouped-server fix and the harness-error runs; they are not counted. The `runs-*.out*` files are the lane logs.
