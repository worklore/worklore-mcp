# Guide-eval round 11: open models a cautious buyer can run, and the story against a plain ticket

Date: 2026-11-09. Written before any run (the one smoke run, `runs/s11-claude-haiku-ticket-r0`, is rep 0 and not a result).

## Why

Valentina's question (2026-11-09): if smaller or open models with the right story do as well as frontier models, worklore
is worth most to teams that can't send code to frontier vendors and run open models in their own network. A second
opinion (Codex GPT-6.1-Sol, Gemini 3.8 Flash, Gemini flash-lite) said the data doesn't show that yet: the one open model in
round 8, GPT-OSS 120B, went from 6 to 18 of 30 with a story, below Opus without one (27 of 30); Kimi reached 30 of 30, but a
2.8-trillion-parameter Chinese model is what those buyers are least likely to run. All three also asked whether the story's
format adds anything over the same facts in a plain ticket, which is what a company already has.

## Questions, and what each answer changes

| | question | measured as | decision rule, fixed now |
|---|---|---|---|
| A | Does an open model a cautious buyer can run reach frontier level with a story? | story arm of codex-oss and vibe-devstral against Opus none-en from round 8 (27/30) | "reaches frontier" when its story arm is 27/30 or more. Below 24/30 (lower than Opus without a story by 10 pp or more): the self-hosted idea has no evidence from this round |
| B | Was round 8's GPT-OSS result the model or its harness? | codex-oss (Codex CLI) against agy-oss (Antigravity, round 8), none and story arms | "harness" when codex-oss beats agy-oss by 20 pp or more on the story arm (18/30 → 24/30 or more) |
| C | Is the value in the story's format or in its facts? | story arm against ticket arm, the four stories that mattered (s1, s3, s7, s10), per agent and pooled | "the facts" when ticket is within 10 pp of story pooled across the four agents; "the format" when story beats ticket by 15 pp or more with a 95% interval above 0 |

If C says "the facts", the product inside a company is drafting the ticket automatically from the fix, not asking
people to write stories, and that changes what to build before any self-hosted version.

## Design

Six stories as in round 8: s1 HR corridors, s3 launchd, s7 Intervals OAuth, s10 keystroke trap, and the two controls s8
cache markers and s11 second write. Same fixtures, graders and English prompts as round 8 (copied here).

Three arms, English task:

| arm | prompt |
|---|---|
| none | the task + the ground rules |
| story | the task + "A colleague's note on a similar case is below..." + the story + the ground rules (= round 8's example-en) |
| ticket | the same, with `tickets/<s>.md` in place of the story |

The ticket holds the story's facts as a colleague's comment on a bug ticket: the symptom, what was tried, the cause, the
fix, the traps, in plain paragraphs, without the reproduction contract (prerequisites, steps, Verify, the check section).
Codex wrote the tickets (`tickets/make_tickets.sh`), so their wording doesn't come from the same model as the stories;
each was checked against its grader's answer key (`tickets/CHECK.md`). Both arms use the same prefix line, so the only
difference is what follows it. Tickets are shorter (2,221 words against 3,630 for the six), which is part of what a
ticket is; the check makes sure no fact the grader needs is missing.

Agents, five repetitions each, repetitions in the outer loop:

| lane | model | harness | runs |
|---|---|---|---|
| claude-haiku | Claude Haiku 5.5 | Claude Code, as round 8 | 90 |
| codex-sol-low | GPT-6-Sol, low | Codex CLI, as round 8 | 90 |
| codex-oss | GPT-OSS 120B (OpenAI, Apache 2.0), medium reasoning | Codex CLI 0.160, OpenRouter Responses API | 90 |
| vibe-devstral | Devstral 2, `mistralai/devstral-2512` (Mistral; modified MIT with a revenue cap) | Mistral Vibe CLI 3.1.0, OpenRouter | 90 |
| kimi-k31 (optional) | Kimi K3.1 Pro (weights open since 2026-11-04) | Kimi Code, as round 8 | 30, ticket arm only |

360 runs (390 with Kimi). The references are rerun on the same days so the ticket comparison is not across a month.
Hosted copies of the open models have the same weights as a self-hosted install; this Mac (16 GB) can't run them locally.

## Differences to say when comparing

- The two OpenRouter lanes run under `open-sandbox.sb` (no reading or writing the real home, no launchctl, security or
  osascript), the env allowlist of `../sandbox/env.sh` plus `OPENROUTER_API_KEY`, and scratch HOME / CODEX_HOME /
  VIBE_HOME. Haiku and Codex low run with the real HOME, as in round 8. On s3, launchctl is blocked for the sandboxed
  lanes; the fixture carries a `launchctl-print.txt` snapshot (the same caveat as Kimi in round 8).
- Web search: Codex's built-in web search is an OpenAI-hosted tool and may not work through OpenRouter; Vibe's
  web_search may need Mistral's own API. Whatever the smoke runs show is written into results.md. No web is also how
  these models would run inside a closed network.
- Vibe stops a run above $1.50 (`--max-price`); such a run counts as a fail, not a redo.
- Vibe runs with `outside_workdir = "deny"` (its headless default "ask" would hang).

## Predictions, so the result can contradict them

- A: codex-oss story arm 22–26/30 (not frontier); vibe-devstral 20–25/30.
- B: codex-oss beats agy-oss on both arms, by 10–20 pp on the story arm (part harness, not all).
- C: ticket close to story for Haiku and Codex low (within 10 pp); story ahead of ticket for the open models on s3 and
  s10, where the contract lists what to check, by 10–20 pp.
- Controls s8 and s11: no arm differs by more than one pass per agent.

## Cost and safety

OpenRouter on 2026-11-09: GPT-OSS 120B $0.15 / $0.60 per million input / output tokens, Devstral 2 $0.40 / $2.00.
Estimate: $10–20 for both lanes. `smoke.sh` runs one paid run per lane first and prints the cost; stop if it is far off.
The key lives in SSM `/worklore/openrouter-api-key` (SecureString) and is read into the lane's environment, never
printed. After every run, `run.sh` scrubs the key value from every file in the run folder (`key_hits` in meta.json);
`make_table.py` lists any run where that happened. A rejected key or no credits writes `STOP-<agent>` and the lane stops.
Before publishing: grep the logs for secret NAME= values, strip nested `.git` and `workdir/`, check launchctl and `~/bin`.

## How to run

    ./smoke.sh                      # one paid run per OpenRouter lane, prints parse checks and cost
    nohup ./all.sh > all.out 2>&1 &  # the four main lanes, about a day
    ./lane.sh kimi-k31               # optional, uses the Kimi plan's 5-hour quota
    python3 make_table.py > table.md

## Amendment, 2026-11-09 evening, before any round run

Two things changed after this plan was written, so the round changes with them.

1. **New stories.** Round 8's no-story runs reached the published stories through Google's search summaries
   (`../round8/exposure.md`), and s1, s3, s7 and s10 are all published and indexed, so a none arm on them is no longer
   clean. Valentina's rules (2026-11-09): eval stories must be unpublished, and a story only goes into a round after it
   changes the weak subscription models' results (`screen.md`). The screen kept three of eight candidates from real work:
   **n4** Codex `-o` under a sandbox (none 1/9 → story 8/9), **n6** Hedera SDK (0/9 → 9/9), **n10** Prisma 8 (3/9 → 9/9).
   They replace s1, s3, s7 and s10. The controls s8 and s11 stay (their story changes little, exposed or not).
2. **References run here, on the new stories.** Round 8 has no cells for n4/n6/n10, so the two references are run in
   this round: `claude-opus` (Opus 5.5, Claude Code, none arm, 15 runs) for A and `agy-oss` (GPT-OSS 120B medium in
   Antigravity, none and story, 30 runs) for B, with round 8's harnesses.

The screen's runs (`screen-runs/`) are not used as round results: they chose the stories, so reusing them would
inflate the effects. Every round cell is a fresh run.

Lanes and runs: claude-haiku, codex-sol-low, codex-oss, vibe-devstral × 5 stories (n4 n6 n10 s8 s11) × 3 arms × 5
reps = 300; claude-opus 15; agy-oss 30. 345 runs, all six lanes in parallel. Kimi is left out (Valentina asked for the
OpenRouter models).

Decision rules, restated for the new stories (fixed now):

| | rule |
|---|---|
| A | on n4, n6, n10 pooled (15 runs per arm): an open model "reaches frontier" when its story arm passes at least as many runs as claude-opus none; "no evidence" when it is 10 pp or more below |
| B | "harness" when codex-oss beats agy-oss by 20 pp or more on the story arm (n4, n6, n10) |
| C | as above, on n4, n6, n10 instead of s1, s3, s7, s10, pooled across the four main agents (60 runs per arm) |

Predictions for the new stories: A, codex-oss story 10–13/15 and vibe-devstral 8–12/15, Opus none 3–6/15 (the stories
were picked because agents without them fail, so A is easier to meet than in the original plan; say so with the
result). B, codex-oss ahead of agy-oss by 0–20 pp. C, ticket within 10 pp of story for all four agents: these three
stories are one fact each, which a ticket carries as well as a story.

Differences to say: n4's task asks for a sandboxed lane, and the OpenRouter lanes already run under `sandbox-exec`, which
can't nest, so those agents can't test their lane end to end (the grader runs it outside). n10 needs the local
PostgreSQL on :5435 (`controls/n10/README.md`); each run gets its own database. The n6, n7, n9 and n10 graders reinstall
from the lockfile when an agent deletes `node_modules`.
