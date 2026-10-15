# Do coding agents still need guides? 56 runs with and without one

Data for the article "Do coding agents still need guides? I ran 4 agents with and without one, 56 times" (October 2026).

Each run gives an agent a task in a fresh copy of a small fixture repo, either with a guide (a worklore story pasted after the task) or without it. Hidden graders implement the guide's own Verify section and read the repo, the diff and the tool-call log, never the agent's own report.

| Round | Folder | Runs | What it tests |
|---|---|---|---|
| 1, technical guides | `./` (`results.md`) | 24 | 3 stories × 4 agents (Claude Code · Opus 5.5, Codex CLI · GPT-6-Sol, Antigravity · Gemini 3.1 Pro, Antigravity · Gemini 3.8 Flash) × with / without |
| 2, a non-technical guide | `marketing-plan/` (`results.md`) | 8 | the 1-Page Marketing Plan skill, same 4 agents × 2 arms, judged blind by 4 models from 3 vendors |
| 3, same model, two harnesses | `harness/` (`results.md`) | 24 | Claude Sonnet 4.6 and Opus 4.6, each in Claude Code and in Antigravity, 2 stories × 2 arms |

Each round's `results.md` has the full tables, analysis, surprises and caveats.

## Layout

- `stories/`, `harness/stories/`: the guide text each WITH run received (the worklore stories as of that day).
- `prompts/`: task prompts and the shared ground-rules line.
- `fixtures/`: the starting repos.
- `graders/`: the hidden graders. `controls/`: graders run on the unmodified fixtures (fail) and on reference fixes (pass).
- `runs/<story>-<agent>-<arm>/`: `prompt.txt`, `agent.log` (structured tool-call stream), `diff.patch`, `grade.json`, `notes.txt`, and the final `repo/`.
- `run.sh`, `lane.sh`, `aggregate.py`, `make_table.py`: the harness and the tables.

## Notes

- One or two samples per cell: strong anecdotes, not a benchmark.
- Paths in the scripts are the author's machine; change them to rerun.
- One agent ran `env` during a run. Secret values in that log (`runs/s1-agy-flash-without/agent.log`) are replaced with `[REDACTED]`; nothing else was edited.
- `results.md` says WORKLORE_TOKEN, WORKLORE_API and GEMINI_API_KEY were unset for every agent. That `env` output shows Antigravity's shell still had them, probably inherited from its background service rather than the launching shell. No run used them: no log contains an authenticated request or a call to the worklore API.
