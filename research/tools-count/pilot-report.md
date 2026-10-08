# Pilot report: tool count vs. accuracy and tokens

Date: 2026-10-07. Claude only (`claude-opus-5-5` in Claude Code 2.1.285). Server sizes N = 5, 25, 50 and GROUPED. Every task, 1 repetition.

The pilot ran twice:
- **pilot1:** 15 tasks, 60 runs.
- **pilot2:** 18 tasks, 72 runs. It came after the fixes below.

Raw runs are in `runs/pilot1/` and `runs/pilot2/`. The tables are `tables-pilot1.md` and `tables-pilot2.md`.

## Self-check

| check | result |
|---|---|
| The call log captures calls | Yes. Every run has `calls.jsonl` from the fake server, with a `start` record (the exposed tool list), `tools/list`, and one record per call: tool, canonical op, args and result. Scoring uses only this log, never the model's own claims. |
| Built-ins are really unavailable | Yes. The init event of every run lists 0 built-in tools (`available_builtins: []`), and every run made 0 built-in calls. A probe run asked the model to list its tools. It named only the `mcp__filekit__*` tools and said it has no shell and no file reader. The user's global CLAUDE.md does not leak into these runs: a probe found no trace of it, and the base context with no tools is about 2.5k tokens. |
| Tokens grow with N as expected | Yes, linearly. First-call input tokens = 3222 + 168.9 × N (R² = 1.000). Input tokens per run = 6995 + 436 × N (R² = 0.999). GROUPED (7 tools) costs 5,480 first-call tokens, about the same as N ≈ 13 separate tools. |
| The task set is not broken | No task fails at N = 5. Every task passes at every N. |
| The task set is not trivial | Accuracy was 100% in every cell. The task allows that only if tokens still differ, and they do (4.1k → 11.7k first-call tokens). Accuracy is the open question for the full run: the other two models and more repetitions. |
| Transcripts spot-read | Six were read: pilot1 GROUPED/t15, 50/t06 and 5/t08; pilot2 GROUPED/t16, 50/t18 and 25/t07. Each took the expected path, picked the right tool and passed the right args. The final sentences were accurate. |

## Problems found and fixed

1. **The fake info tools contradicted the edit tools** (found in pilot1 transcript GROUPED/t15). `image_info` returned 4032×3024 with GPS data for every file, so after a successful resize the model "verified" the result, saw no change, and retried the resize. The same flaw in `pdf_info` sent Codex and Gemini into verify-and-retry loops in smoke runs. Gemini ran 28 calls and hit the 180 s timeout on the new t16.
   **Fix:** the server now keeps per-run file state. Each edit writes the properties of its output: size, dimensions, EXIF, page count, rotation, encryption, linearization, title and author. `pdf_info` and `image_info` report that state, so verification now agrees with what the model did.
2. **The task set was easy for Opus.** Pilot1 got 15/15 in every cell. Three harder ambiguous tasks were added:
   - t16: "clear the author and title of report.pdf". The tempting neighbour is `image_strip_metadata`.
   - t17: "remove pages 2 and 5". Neighbours: `pdf_extract_pages`, `pdf_split`.
   - t18: "page 3 was scanned upside down". Neighbours: `image_rotate`, `pdf_reorder_pages`. This task also needs the right args: 180° and page 3 only.
   A `pageset` arg check was added for t17 and t18.
3. **Isolation hardening** (before the pilot):
   - The server is copied to `/tmp/filekit-mcp/server.py`, a neutral path with no answer key beside it.
   - The runner passes the task's needed tools as `TC_NEED`, so the server never opens `tasks.json`.
   - Call logs go to `/tmp/fk-*.jsonl` and are moved into the run folder afterwards.
   - Agents work in a fresh `/tmp/work-XXXXXX` folder, which is deleted after the run.

## Design decisions to note

- **The exposed set is built per task.** At size N, the server exposes the task's own needed tools (1–3 of them), then fills up to N with distractors. Distractors are taken in a fixed seeded order (seed 20261007) over the whole 50-tool pool, so each N is a superset of the smaller one.
  - The union of needed tools across all 18 tasks is 19. If one global set had to contain all of them, the sweep could not start below 19.
  - With per-task sets, N = 5 is solvable for every task, and the sweep starts at 5 as asked.
  - The tempting neighbours of a task enter at different N values. `neighbors_present` in each row records which ones were exposed.
- **GROUPED has 7 tools, not 6:** `doc_read`, `doc_convert`, `pdf_edit{operation}`, `pdf_info`, `image_edit{operation}`, `qr_make` and `archive{operation}`. Ashton's six nouns had no place for the zip operations, which the pool includes (`zip_create`, `zip_extract`, `zip_list`). The 7 tools cover all 50 operations; this is checked in code. Each grouped call is mapped to its canonical separate op for scoring.
- **Each harness exposes MCP tools differently.** This came out of the setup work and matters for the full run:
  - **Claude Code** sends every MCP tool's full schema to the model as a native tool definition. That is why the cost is linear at about 169 tokens per tool.
  - **Codex CLI 0.160** (default model `gpt-6.1-sol`, default reasoning effort) runs in "code mode". The model gets one `exec` tool, a JS runtime, and calls `tools.mcp__filekit__X(...)` from inside it. The MCP tool declarations sit inside that tool's description, and the model can search `ALL_TOOLS` with code. "Astra" is not what `codex` defaults to here, so the default model was used and its id is recorded per run from the session file.
  - **Antigravity (`agy` 1.2.17)** loads MCP tools lazily. The system prompt lists only the tool names. The model reads each tool's JSON schema from a cache file with `view_file`, then calls it through a generic `call_mcp_tool`. So its context grows only by names, plus the schemas it chooses to read.
- **Antigravity isolation.** A workspace plugin carries the MCP server, and a custom main agent (`.agents/agents/assistant.md`) keeps only `view_file`, which the lazy schemas need. Its tool list is then: `view_file`, `call_mcp_tool`, `list_resources`, `read_resource` and `manage_task`. There is no shell, no file write and no web.
  - `view_file` is a file-read built-in. That is a deviation from "no file built-ins", but Antigravity cannot use MCP tools without it.
  - Every `view_file` call outside the schema cache counts as a built-in call in the CSV.
  - The schema cache (`~/.gemini/antigravity-cli/mcp/filekit_filekit/`) is global, so Gemini runs are sequential, with the cache cleared before each run.
  - If a custom agent's frontmatter is invalid, Antigravity silently falls back to the default agent, which has a shell. The scorer would catch that as built-in calls.
- **Gemini is the real Pro model**, `gemini-3.1-pro-high` through the Google AI Pro subscription in `agy`. The API-key flash-lite substitute was not needed.

## Verdict

The pilot is clean. The full run was launched at 17:42 with:
- 3 models × N ∈ {5, 10, …, 50} + GROUPED × 18 tasks × 2 repetitions = 1,188 runs;
- Claude and Codex at 2 runs at a time each, Gemini sequential;
- a 6-hour budget guard.

## Addendum: the 75/100 extension

After the full run, the owner asked to extend the sweep past 50. The pool grew to 100 tools: 50 look-alike-rich extension tools, appended after the original seeded order. `verify_compat.py` confirms that every N ≤ 50 and GROUPED is byte-identical to the 50-tool server. N = 75 and 100 were then run for all three models (216 runs). See "What happens at 100" in `report.md`.
