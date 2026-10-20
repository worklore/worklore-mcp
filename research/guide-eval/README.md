# Do coding agents still need guides? 271 runs with and without one

Data for the article "Do coding agents still need guides? 271 runs, 9 agents, with and without one" (October 2026).

Each run gives an agent a task in a fresh copy of a small fixture repo, either with a guide (a worklore story pasted after the task) or without it. Hidden graders implement the guide's own Verify section and read the repo, the diff and the tool-call log, never the agent's own report.

| Round | Folder | Runs | What it tests |
|---|---|---|---|
| 1, technical guides | `./` (`results.md`) | 24 | 3 stories × 4 agents (Claude Code · Opus 5.5, Codex CLI · GPT-6-Sol, Antigravity · Gemini 3.1 Pro, Antigravity · Gemini 3.8 Flash) × with / without |
| 2, a non-technical guide | `marketing-plan/` (`results.md`) | 8 | the 1-Page Marketing Plan skill, same 4 agents × 2 arms, judged blind by 4 models from 3 vendors |
| 3, same model, two harnesses | `harness/` (`results.md`) | 24 | Claude Sonnet 4.6 and Opus 4.6, each in Claude Code and in Antigravity, 2 stories × 2 arms |
| 4, tasks asked the way a person types them | `round4/` (`results.md`) | 16 | the skills review asked as "are these safe?" (no tier) and a 3NF audit of a real schema; 4 agents (Gemini 4 Argon replaces 3.1 Pro) × 2 arms |
| 5, which kinds of guide help, and how to hand one over | `round5/` (`plan.md`, `results.md`, `table.md`) | 207 of 216 | 6 stories sorted by what they carry (niche fact, fact from the docs, two traps, a trap, a derivable cause, a method) × 9 agent configurations (Claude Opus/Sonnet/Haiku 5.5, Codex gpt-6-sol medium/low, Gemini 4 Argon high/low, Gemini 3.8 Flash, GPT-OSS 120B) × 4 arms: no guide, "Follow this guide", "a colleague's note, use what applies", and the guide unmentioned in a `notes/` folder. 9 Gemini 4 Argon runs never started (quota) |

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
- One agent ran `env` during a run. Secret values in that log (`runs/s1-agy-flash-without/agent.log`) are replaced with `[REDACTED]`; nothing else was edited. The same happened in `round4/runs/s1-agy-flash-*` and, through `env -i zsh` re-reading the login files, in `round5/runs/s3-agy-argon-high-none-r1`; same treatment.
- Rounds 4 and 5 ship each run without its scratch working copy (`workdir/`) and without the nested `.git` of the final `repo/`; `diff.patch` is the agent's change against `base_commit`. Round 5 runs that Antigravity's GPT-OSS answered outside the repo have the answer under `grade.json` → `answer_source: brain`.
- `results.md` says WORKLORE_TOKEN, WORKLORE_API and GEMINI_API_KEY were unset for every agent. That `env` output shows Antigravity's shell still had them, probably inherited from its background service rather than the launching shell. No run used them: no log contains an authenticated request or a call to the worklore API.

| 6 | 2026-10-20 | the skills task asked as "what can each skill touch" (round 4 had asked "is it safe?") | 4 agents × with/without, 8 runs (7 completed; Argon quota) | 7 / 7 pass on disclosure; the guide added tier + hash per finding | `round6/` |
