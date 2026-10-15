# How many MCP tools is too many? A measured answer

1,656 scored runs: three agents (Claude Code with Claude Opus 5.5, Codex CLI with
gpt-6.1-sol, Antigravity with Gemini 3.1 Pro) against one fake MCP server that
exposes 5 to 100 tools, plus a grouped variant (7 multi-operation tools covering
the same 50 operations). Claude Code was measured twice: with MCP tool search on
(its default) and off. 18 tasks with known answers, 10 of them ambiguous, 2
repetitions per cell. October 2026.

**Short version** (details, charts and every limitation in [report.md](report.md)):

- **Accuracy did not drop with separate tools, from 5 up to 100**: 1,296 of 1,296
  runs fully correct (right tools, order and key arguments), plus 252 of 252 for
  Claude Code with tool search on, including the tasks where a look-alike tool
  was one name away.
- **The cost of more tools depends on the client, not the model.**
  - **Claude Code, default (tool search on):** MCP tools are deferred; only names
    go into the prompt and the model loads what it needs with `ToolSearch`. First
    call 3.9k → 4.6k → 5.4k input tokens at 5 / 50 / 100 tools; per run
    13.8k → 17.4k → 19.9k. Every run made exactly one `ToolSearch` call, by
    exact name, and the search never hid the right tool.
  - **Claude Code, tool search off** (`--tools ""`, `ENABLE_TOOL_SEARCH=false`, or
    a proxy without tool-reference support): every schema on every call, +169
    input tokens per tool, linear. First call 4.1k → 11.7k → 20.2k; per run
    9.3k → 27.9k → 48.6k.
  - So tool search costs more at small N (one extra model call: +48% input at 5
    tools), breaks even at about 19 tools, and saves 59% of per-run input at 100.
    At list price it was not cheaper in these one-task runs ($0.047 vs $0.038 per
    run at 100), because nearly all input is cache reads and the search adds a
    call, output and cache writes; what it saves is context.
  - Codex keeps schemas out of the prompt and searches them with code (flat first
    call, but its search output was truncated at 100 tools). Antigravity sends
    only names (~5 tokens per tool).
- **Do names decide? Not the choice, but the reading.** The same 100 tools renamed to
  vague names (`optimize_file`, `process_image`, `convert_document`, …; look-alikes get
  look-alike names) were still picked right in 276 of 276 runs, because the
  descriptions decided. Under deferred loading, though, the agent had to read more first.
  Claude Code (default) loaded 3–5× as many schemas and used keyword searches,
  with +21% input at 100 tools. Gemini opened a wrong schema first in 34 of 72 runs
  and probed wrong tools with empty arguments, with +38% input. With every schema
  upfront (tool search off), names changed nothing.
- **Grouping helps or hurts depending on the client**: the cheapest option in
  Claude Code with tool search off (7 grouped tools cost about as much as 14
  separate ones), little difference with tool search on, and the only accuracy
  drop anywhere in Antigravity (89%).
- **The cheapest models** (added 2026-10-14, 1,404 more runs, phase `cheap`): Claude
  Haiku 5.5 in Claude Code (tool search off), GPT-Reserve in Codex CLI, Gemini 3.8
  Flash (low) in Antigravity, same tasks and sizes. Separate tools: 1,288 of 1,296
  fully correct (Haiku 432/432, GPT-Reserve 428/432, Gemini Flash 428/432). This is
  the first time a wrong tool was executed with separate tools: GPT-Reserve in 4 runs
  (at 40, 45 and twice at 100). 3 of Gemini Flash's 4 misses are API rejections of an
  integer-enum schema, not model choices. Per-run input grows faster than with the
  frontier models (GPT-Reserve +655 tokens per tool vs +408; Haiku +488 vs +429).
  Grouped: Haiku 34/36, GPT-Reserve 36/36, Gemini Flash 35/36. Haiku cost $0.0012 per
  run. Tables in [tables-cheap.md](tables-cheap.md), charts `charts/*-cheap.png`,
  runner `night-cheap.sh` (`MODEL_ID` picks the model per client).

## What's here

| File | What |
|---|---|
| [report.md](report.md) | the write-up, including "What happens at 100" |
| [pilot-report.md](pilot-report.md) | the pilot, the self-checks and the fixes made before the full run |
| [vague-names.json](vague-names.json) | the vague-name mapping (`TC_NAMES=vague`); results in [tables-vague.md](tables-vague.md) and `charts/names-*.png` |
| [charts/](charts/) | accuracy, tokens, wrong picks on ambiguous tasks, time — all vs tool count |
| [results.csv](results.csv) | one row per run, scored from the server's own call log |
| [server.py](server.py) | the fake MCP server (Python stdlib, stdio): 100 tools, grouped variant, per-run call log |
| [tasks.json](tasks.json) | the 18 tasks and their expected calls |
| `run.sh`, `job.sh`, `lane.sh`, `score.py`, `analyze.py`, `make_report.py` | runner, scorer and analysis (`run.sh claude` = tool search off, `run.sh claude-search` = on) |
| `runs.tar.gz` | every raw run (transcripts, call logs), 32 MB packed |

The tools are fake (nothing touches a file), the tasks come from one domain
(files and documents), and token counts include each client's own overhead, so
compare growth within one client rather than absolute numbers between clients.

Run it on your own machine: see the runner section in [report.md](report.md).
Part of [worklore](https://worklore.dev), stories developers' agents can reproduce.
