# Paste fidelity: what arrives when an agent pastes a file into an MCP tool

216 headless runs, 2026-10-14/15: three agents (Claude Code · Opus 5.5, Codex CLI · default model, Antigravity · Gemini 3.8 Flash high) ask worklore's `check_capability` to scan a local `SKILL.md`. 8 public skills (1.2–75 KB, copies from [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official), sources in `urls.json`), 3 reps each, three phases:

- `before` — the tool took only pasted `text` (MCP 0.6.x)
- `after-file` — MCP 0.7.0 (`url` for GitHub without sign-in, `received.text_sha256`, `expected_sha256`), same prompt
- `after-url` — MCP 0.7.0, and the prompt names the GitHub URL the skill came from

`proxy.py` is a stdio MCP proxy that forwards to worklore.dev and logs every call's arguments, so `score.py` compares exactly what arrived with the file byte for byte.

Results: `summary.md` (tables + every non-exact run with a diff) and `results.csv` (one row per run). Transcripts: `runs.tar.gz` → `runs/<phase>/<agent>/<skill>-r<rep>/` (agent.log, calls.jsonl, row.json, meta.json).

Headline: Claude Code paid $1.03 and 187 s (27.6k output tokens) to paste the 75 KB file; with a URL it was $0.25 and 21 s. Codex never pasted (code mode passes a variable) and sent `expected_sha256` in 48/48 runs after the change. Gemini changed a final newline 3/3 on one file and never finished the 75 KB check until it could pass the URL.

Story: https://worklore.dev/s/2026-10-15-cut-claude-code-token-cost-4-let-your-mcp-tool-take-a-url-in
Reproduce: `batch.sh` (set `PHASES`), then `python3 summarize.py`. Paths in the scripts are the author's machine; change `D=`.
