# Round 11 results

Run 2026-11-09 22:08 to 2026-11-10 04:02, all six lanes in parallel (`all.sh`), 345 runs. Tables: `table.md`
(`python3 make_table.py`). Rules and predictions: `plan.md`, the amendment of 2026-11-09 evening (written before any round
run). Stories: n4, n6, n10 (chosen by `screen.md`) and the controls s8, s11.

## Answers to the three questions

| | rule (plan.md amendment) | result | answer |
|---|---|---|---|
| A | an open model "reaches frontier" when its story arm on n4/n6/n10 passes at least as many runs as claude-opus none; "no evidence" at 10 pp or more below | Opus none 7/15. vibe-devstral story 12/15 (+33 pp, 95% CI 0 to +67). codex-oss story 6/15 (−7 pp, CI −40 to +27) | Devstral 2 reaches frontier on these tasks. GPT-OSS 120B is between the two thresholds: not frontier, and not 10 pp below |
| B | "harness" when codex-oss beats agy-oss by 20 pp or more on the story arm | codex-oss story 6/15, agy-oss story 7/15 (−7 pp, CI −40 to +27); none arm 0/15 and 0/15 | Not the harness. GPT-OSS does no better in Codex CLI than in Antigravity |
| C | "the facts" when ticket is within 10 pp of story pooled over the four main agents; "the format" when story beats ticket by 15 pp or more with a CI above 0 | story 48/60, ticket 47/60, +2 pp (CI −13 to +17). Per agent: Haiku 15/15 vs 15/15, Codex low 15/15 vs 15/15, codex-oss 6/15 vs 6/15, Devstral 12/15 vs 11/15 | The facts |

As the amendment says, A is easier to meet than in the original plan: the three stories were picked because agents
without them fail. Opus was not part of the screen, and its none arm on these stories (7/15) is the reference, not a
screened number.

## Predictions against results

| prediction (amendment) | result | held |
|---|---|---|
| A: codex-oss story 10–13/15 | 6/15 | no, lower |
| A: vibe-devstral story 8–12/15 | 12/15 | yes |
| A: Opus none 3–6/15 | 7/15 | no, one higher |
| B: codex-oss ahead of agy-oss by 0–20 pp | 7 pp behind | no |
| C: ticket within 10 pp of story for all four agents | 0, 0, 0, +7 pp | yes |
| Controls (plan.md): no arm differs by more than one pass per agent | Devstral on s8: none 1/5, story 5/5, ticket 5/5 | no, for Devstral on s8; all other control cells hold |

## What the passes and fails were

- **Package choice (n6, n10).** Runs that picked the current package (`@hiero-ledger/sdk`, Prisma 8): without a note 7
  of 60 (Opus 3/10, Devstral 2/10, Codex low 1/10, codex-oss 1/10, Haiku 0/10, agy-oss 0/10); with the story or the
  ticket 87 of 90 (Haiku, Codex low and Devstral 20/20, codex-oss 19/20, agy-oss 8/10).
- **Works on the old package.** Without a note, Haiku and Codex low built working code on the old package in 18 of 20
  runs (n6 WORKS_ON_OLD_SDK 9/10, n10 WORKS_ON_PRISMA7 9/10); Opus in 7 of 10 (n6 2/5, n10 5/5). Every Prisma 7 run read
  the dist-tags, saw `prisma@latest` = 8.0.0-rc.33 and `@prisma/client@latest` = 7.10.1, and pinned 7.10.1 on the
  rule that CLI and client versions must match; Opus and Haiku said so in ANSWER.md.
- **Opus on n6** checked both package names in its first command in the three runs that passed (no web use in any
  Opus run).
- **GPT-OSS with a note** picked the right package in 27 of 30 runs (both harnesses) and then failed the task itself
  (wrong transaction ID or amounts on n6, a script or tables that didn't work on n10).
- **Devstral on n6**: all 10 story and ticket runs on `@hiero-ledger/sdk`. Story arm 2/5: two runs hit the
  `--max-price` cap (exit 3) with no working result, one printed wrong output. Ticket arm 1/5: four runs hit the cap,
  and three of those had already left a result the grader passes (PASS true, exit 3). By the pre-registered rule they
  count as fails, so the ticket arm is 1/5 (graded alone it would be 4/5; Devstral's ticket cell on n4/n6/n10 would be
  14/15 instead of 11/15, and C pooled 50/60 against story 48/60, which doesn't change the answer). These three are the
  only runs in the round graded pass with a nonzero exit. Without a note, 4 of 5 none runs hit the cap; all 5 were on
  the old `@hashgraph/sdk`.
- **n4**: without a note only Opus (4/5) and Haiku (1/5) built a lane that returns the answer; with a note every agent
  but codex-oss (4/5 story, 3/5 ticket) did 5/5.

## Runs that were redone or don't count

- Outages redone (marked `limit`, rerun by `lane.sh` passes): agy-oss "No capacity available for model
  gpt-oss-120b-medium" (several cells, n10 none r2 needed four passes); codex-oss OpenRouter `upstream returned 502`
  (s8 none r2, s11 none r2, s8 ticket r3; `run.sh` detects this pattern since 2026-11-10 01:1x, the two earlier runs
  were marked by hand); codex-sol-low n6 ticket r3 (usage limit).
- Timeouts (exit 124, 1200 s) count as fails: listed in `table.md`.
- Vibe exit 3 = `price_limit`, counted as fails (plan.md: "Vibe stops a run above $1.50; such a run counts as a fail,
  not a redo"). Vibe's `cost_usd` is its own list-price estimate; the real OpenRouter spend is lower because of caching.

## Cost

OpenRouter credit used, all lanes and the smoke runs together: $7.98 of $25 (checked 2026-11-10 04:05). Vibe's own
estimate for its 75 runs is $26.60 (table.md), so its list-price estimate is several times the real spend.

## Web use

No none-arm run of Haiku, codex-oss, Devstral or Opus used the web. Codex low searched in 1 none run, agy-oss in 4; the
stories were not on the web, so no run could reach them.

## Safety checks after the round (2026-11-10 04:05)

- OpenRouter key: found in no run file (`key_hits` 0 everywhere, fixed-string grep 0).
- `~/.codex/config.toml`: changed only by 76 trust entries for this round's codex-sol-low run folders (75 runs plus
  one outage run that was redone); with them removed the file hashes as before the round (`c6cc2e41…`), and the real
  file was restored to that content. `models_cache.json` was refreshed by Codex.
- Nothing new in `~/bin`, `~/Library/LaunchAgents` or the user launchctl jobs.
- Leftovers in `/tmp` from agents (a test file, an empty scratch home, and a copy of the n10 fixture's local test
  `DATABASE_URL` that a Haiku ticket run moved out of its repo) were removed.
- n10 PostgreSQL on :5435 stopped; every per-run database was dropped by the grader.
- Before publishing: strip nested `.git` and `workdir/` from `runs/` and `screen-runs/`; `graders/n6_keys.txt` holds
  test-only keys.
