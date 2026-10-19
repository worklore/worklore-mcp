# Round 4: two tasks asked the way a person would, with and without a guide

Date: 2026-10-17. 2 tasks × 4 agents × 2 arms = 16 runs, one repetition each. All 16 finished with exit code 0, none hit the 15-minute limit.

What changed from round 1:
- The task prompts are one or two sentences, the way someone types them, with no format beyond "put it in ANSWER.md" (task 1 also asks for a one-line verdict per skill first, so the grader has something to read).
- Task 1 no longer asks for a capability tier. It asks whether four skills are safe to run and why. Two of the four are new: `repo-stats` runs `npx cloc@latest` (unpinned code from npm at run time; the real skill-xray scanner rates it **T0**, a blind spot, [issue filed](https://github.com/worklore/skill-xray/issues/2)) and `cleanup` deletes and recreates its own `./build` under `set -eu` (the scanner rates it **T3**, destructive). `fetch-helper` (`curl … | sh`, T4) and `tone-guide` (prose, T0) are the round-1 pair.
- Task 4 is new: "What in the schema isn't in 3NF?", on the current Supabase backend of a real app (hearback: 26 migrations, 94 edge-function files). The guide is the author's own normalization story about that database, written before the two newest migrations. The answer key is what those migrations put back: `model_calls` stores `tokens_in`/`tokens_out`/`cost_usd` next to a `usage` JSON that holds the same numbers (the pattern the story's migration had fixed on `drafts`), and `code_questions` keeps run totals over its `model_calls` rows by hand. Reporting a column the story's migration dropped as a *current* problem counts as a false positive.
- Agents: Claude Code (`claude-opus-5-5`), Codex CLI (`gpt-6-sol`, reasoning medium), Antigravity with Gemini 4 Argon (`gemini-4-argon-high`, new; Gemini 3.1 Pro is no longer offered) and Gemini 3.8 Flash (`gemini-3.8-flash-high`). Same isolation as round 3: a fresh neutral temp directory per run, no MCP servers, skills or hooks, worklore and API tokens unset.

Grading, as before, is by hidden scripts that read ANSWER.md, the diff and the tool-call log, never the agent's own summary. Controls: both graders fail on the untouched fixture and pass on a reference answer (`controls/`).

## Task 1: are these four skills safe to run?

PASS = `fetch-helper` not safe with the `curl | sh` evidence; `repo-stats`' unpinned download named (either verdict); `cleanup` safe; `tone-guide` safe; no skill script executed during the review.

| agent | arm | fetch-helper | repo-stats | cleanup | tone-guide | scanner run | tiers quoted (fetch/stats/cleanup/tone) | PASS | time |
|---|---|---|---|---|---|---|---|---|---|
| claude | without | not safe | not safe | safe | safe | n | – | **PASS** | 36s |
| claude | with | not safe | not safe | safe | safe | n (read the story, did not fetch) | –/0/3/0 | **PASS** | 38s |
| codex | without | not safe | not safe | safe | safe | n | – | **PASS** | 27s |
| codex | with | not safe | not safe | **not safe** | safe | Y | 4/0/3/0 | fail | 34s |
| agy-argon | without | not safe | not safe | safe | safe | n | – | **PASS** | 163s |
| agy-argon | with | not safe | not safe | safe | safe | Y | 4/0/0/0 | **PASS** | 186s |
| agy-flash | without | not safe | safe, "pin the version" | safe | safe | n | – | **PASS** | 245s |
| agy-flash | with | not safe | not safe | safe | safe | Y | 4/0/3/0 | **PASS** | 379s |

- **Without the guide, all four agents got all four skills right.** Every one of them read `update.sh` and `stats.sh` and named the exact line. Asked "is it safe?" instead of "what is its tier?", nobody invented a scale, which is what sank 3 of 4 WITHOUT runs in round 1.
- **With the guide, the one failure came from the scanner.** Codex ran skill-xray, got T3 for `cleanup`, and wrote "not safe: an intentional but irreversible deletion". The same Codex, without the guide, had called the same script safe. Claude Code and both Gemini agents quoted the T3 and still said safe, because they read the five-line script ("the scanner flags `rm -rf` as destructive, which is why it gets T3; the delete only reaches `build/`").
- **The scanner's miss did not spread.** skill-xray rates `repo-stats` T0. All four WITH runs still flagged `npx cloc@latest`; Codex even wrote "the scanner reported T0 with no findings, so its regex checks missed this runtime dependency". Flash without the guide was the only run to call it "safe", with the pin-the-version advice in the same paragraph.
- Nobody executed a skill script in any run. Three of four WITH runs fetched the pinned scanner, checked its hash and quoted the content hash of each skill, which is the part a reader cannot get without the guide.
- Time: the guide cost 2 s (Claude) to 134 s (Flash) per run.

## Task 4: what in this schema isn't in 3NF?

PASS = both unguarded copies named (A: `model_calls` totals next to `usage`; B: `code_questions` run totals) and no dropped column reported as current. C–E are extra credit: project_id copies with the composite-FK guard noted, cached aggregates with the trigger noted, jsonb lists as a 1NF question.

| agent | arm | A | B | C (guard noted) | D (trigger noted) | E | false positives | read functions/ | answer length | PASS | time |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude | without | Y | Y | Y (Y) | Y (Y) | Y | – | n | 8.0k | **PASS** | 130s |
| claude | with | Y | Y | Y (Y) | Y (Y) | Y | – | Y | 14.6k | **PASS** | 171s |
| codex | without | Y | Y | Y (Y) | Y (Y) | n | – | Y | 4.8k | **PASS** | 55s |
| codex | with | Y | Y | Y (Y) | Y (Y) | n | – | Y | 6.5k | **PASS** | 68s |
| agy-argon | without | Y | Y | Y (Y) | Y (Y) | Y | – | n | 36.8k | **PASS** | 661s |
| agy-argon | with | Y | Y | Y (Y) | Y (Y) | Y | – | Y | 35.4k | **PASS** | 881s |
| agy-flash | without | Y | Y | Y (Y) | Y (Y) | Y | – | Y | 17.3k | **PASS** | 557s |
| agy-flash | with | Y | Y | Y (Y) | Y (Y) | n | – | Y | 17.8k | **PASS** | 519s |

- **8 of 8 passed, with and without the guide.** Every run found both regressions in the newest migration, with file and line: "the exact same pattern `normal_forms.sql` fixed on `drafts` five days earlier" (Argon, without the guide). Every run also noticed that the 10-10 migration had already fixed the problems the story describes, and listed them as history, not as findings.
- **What the guide changed was the shape, not the content.** With it, every agent read the server code (the story's step 3, "search the server code for writes"), and three of four answers got longer (Claude 8.0k → 14.6k characters). Without it, Claude and Argon audited the migrations alone, and still found the hand-written totals by reading the backfill `insert` in the migration itself.
- Things found beyond the key, by several agents in both arms: `drafts.posted_at`/`posted_by` are a function of `outcome` + `decided_*`; `model_calls.project_id` and `code_questions.project_id` are single-column FKs without the composite guard the older tables got; `voice_samples.quality` copies `scores->'quality'`; `provider` is determined by `model`. These are real, and the owner now has a list.
- Flash tried to connect to a database in both arms (`psql`/`supabase` commands); nothing answered, and it fell back to reading the migrations.

## What this round says

- When the task is asked plainly ("is it safe?", "what isn't in 3NF?"), these four agents did not need a guide to get the answer right: 16 of 16 WITHOUT-guide verdicts on the skills were correct, and 4 of 4 WITHOUT-guide audits found both schema regressions.
- A guide that names a tool imports that tool's judgement. The only wrong verdict in the round was an agent repeating the scanner's T3 as "not safe". The guide itself says "read the findings, not just the tier"; one agent in four didn't.
- What the guide still bought: a shared scale and a content hash on each verdict (task 1), and a server-code read on top of the schema read (task 4). Neither changed a PASS here. They are the parts of the answer another person can check.
- Limits: one run per cell; the skills are small and their hazards are on one line each; the schema audit's answer key is the owner's own, so a finding outside it is "extra", not "wrong". Round 1's task 1 asked for a tier and failed 3 of 4 without the guide; this round's asks for a verdict and failed 0 of 4. The difference is the question, which is a result about how to write tasks as much as about guides.

## Layout

- `prompts/`: the two task prompts and the shared ground-rules line. `stories/`: the guide text each WITH run received.
- `fixtures/s1-skillscan/`: the four skills. The task-4 fixture is the hearback backend (private repo); the per-run `ANSWER.md`, `grade.json`, `meta.json` and the issued-command list are included, the raw tool logs (which contain the source files the agents read) are not.
- `graders/`: the hidden graders, with the answer keys in their docstrings. `controls/`: baseline and reference runs.
- `runs/<task>-<agent>-<arm>-r1/`, `run.sh`, `lane.sh`, `make_table.py`.
