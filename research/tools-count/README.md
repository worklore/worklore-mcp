# How many MCP tools is too many? A measured answer

1,404 scored runs: three agents (Claude Code with Claude Opus 5.5, Codex CLI with
gpt-6.1-sol, Antigravity with Gemini 3.1 Pro) against one fake MCP server that
exposes 5 to 100 tools, plus a grouped variant (7 multi-operation tools covering
the same 50 operations). 18 tasks with known answers, 10 of them ambiguous, 2
repetitions per cell. October 2026.

**Short version** (details, charts and every limitation in [report.md](report.md)):

- **Accuracy did not drop with separate tools, from 5 up to 100**: 1,296 of 1,296
  runs fully correct (right tools, order and key arguments), including the tasks
  where a look-alike tool was one name away.
- **The cost of more tools depends on the client, not the model.** Claude Code
  with tool search OFF sends every schema on every call: +169 input tokens per
  tool, linear (9.3k tokens per run at 5 tools, 48.6k at 100).
  **Correction (2026-10-08):** these Claude Code runs used `--tools ""`, which also
  disables the `ToolSearch` built-in, so Claude Code fell back to loading every
  schema upfront. By default tool search is ON and MCP tools are deferred: at 100
  tools the first call is 5.5k input tokens instead of 20.3k. A default-mode rerun
  is in progress and will be added here. Codex keeps schemas out of the
  prompt and searches them with code (flat first call, but its search output was
  truncated at 100 tools). Antigravity sends only names (~5 tokens per tool).
- **Grouping helps or hurts depending on the client**: the cheapest option in
  Claude Code (7 grouped tools cost about as much as 14 separate ones), and the
  only accuracy drop anywhere in Antigravity (89%).

## What's here

| File | What |
|---|---|
| [report.md](report.md) | the write-up, including "What happens at 100" |
| [pilot-report.md](pilot-report.md) | the pilot, the self-checks and the fixes made before the full run |
| [charts/](charts/) | accuracy, tokens, wrong picks on ambiguous tasks, time — all vs tool count |
| [results.csv](results.csv) | one row per run, scored from the server's own call log |
| [server.py](server.py) | the fake MCP server (Python stdlib, stdio): 100 tools, grouped variant, per-run call log |
| [tasks.json](tasks.json) | the 18 tasks and their expected calls |
| `run.sh`, `job.sh`, `lane.sh`, `score.py`, `analyze.py`, `make_report.py` | runner, scorer and analysis |
| `runs.tar.gz` | every raw run (transcripts, call logs), 13 MB packed |

The tools are fake (nothing touches a file), the tasks come from one domain
(files and documents), and token counts include each client's own overhead, so
compare growth within one client rather than absolute numbers between clients.

Run it on your own machine: see the runner section in [report.md](report.md).
Part of [worklore](https://worklore.dev), stories developers' agents can reproduce.
