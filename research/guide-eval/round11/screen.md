# Round 11 story screen

Date: 2026-11-09. Written before any screen run.

## Why

Round 8's four stories that mattered (s1, s3, s7, s10) are published and in Google. In round 8, 33 runs without the story
got it through search anyway, 19 of them through Google's own search summary in Gemini's tool (`round8/exposure.md`,
`round8/search-channel.md`), so blocking worklore.dev would not keep a no-story arm clean. Round 11 therefore needs new,
unpublished stories. Valentina's rule (2026-11-09): a story goes into a round only if it changes the result of the weak
subscription models; a story that doesn't is not worth the other runs.

## Candidates

All five come from real work on 2026-11-09 and are not on worklore or anywhere else as a story. The story text is only
in the prompt; nothing is published until the round is done.

| id | kind | the fact |
|---|---|---|
| n1 | fact on no web page | Mistral Vibe CLI with no MISTRAL_API_KEY looks in the macOS Keychain, so under a sandbox it stops |
| n2 | dropped while building | Codex CLI 0.160 rejects wire_api "chat", but its error message names the fix ("set wire_api = \"responses\""), so nothing is hidden; model_context_window does not remove the GPT-OSS metadata warning |
| n3 | trap in natural code | `aws s3 sync --delete` in a prerendered-site deploy takes every page offline during the deploy |
| n4 | trap in natural code | Codex `-o` under a sandbox that denies the run folder fails to write but exits 0 |
| n5 | dropped while building | Antigravity keeps Google search summaries only in its conversation store: with a sample store in the fixture the agent greps its way there (a derivable cause), without one it would have to read the real store in the home folder |

The two controls s8 and s11 stay as they are: their fact is in the docs or the log, so exposure changes little, and
no change is their job.

## Design

Agents: claude-haiku, codex-sol-low, agy-flash-low (the weak models the subscriptions cover, same harnesses as round 8).
Arms: none and story (English task). Three repetitions per cell, repetitions in the outer loop: 18 runs per candidate.

## Keep rule, fixed now

A candidate is kept when all three hold:

1. pooled over the three agents, the story arm passes at least 4 more runs of 9 than the none arm (e.g. 2/9 to 6/9);
2. at least two of the three agents pass more runs with the story than without;
3. the none arm passes at most 6 of 9 (7/9 or more without the story means the agents already know it or find it).

A run that fails because the harness broke (limit, outage) is redone, not counted. If fewer than three candidates are
kept, the round stops there and the result is reported before any OpenRouter run.

## Also recorded per run

Whether the agent searched the web, and whether any search or fetch reached the story's fact (round 8's `exposure.py`
logic), so a none-arm pass can be told apart from a lucky guess.

## Result (2026-11-09, 14:28 to 16:18, 54 runs)

No run hit a limit or an outage, so nothing was redone. No run searched or fetched the web (no WebSearch, WebFetch,
search_web, read_url_content or Codex web_search call in any log), so every none-arm result is the agent on its own.

| candidate | agent | none | story |
|---|---|---|---|
| n1 | claude-haiku | 3/3 | 3/3 |
| n1 | codex-sol-low | 3/3 | 3/3 |
| n1 | agy-flash-low | 3/3 | 3/3 |
| n3 | claude-haiku | 3/3 | 3/3 |
| n3 | codex-sol-low | 3/3 | 3/3 |
| n3 | agy-flash-low | 3/3 | 3/3 |
| n4 | claude-haiku | 1/3 | 2/3 |
| n4 | codex-sol-low | 0/3 | 3/3 |
| n4 | agy-flash-low | 0/3 | 3/3 |

| candidate | none, pooled | story, pooled | rule 1 (+4) | rule 2 (2 of 3 agents) | rule 3 (none ≤6/9) | kept |
|---|---|---|---|---|---|---|
| n1 | 9/9 | 9/9 | no | no | no | no |
| n3 | 9/9 | 9/9 | no | no | no | no |
| n4 | 1/9 | 8/9 | yes (+7) | yes (3 of 3) | yes | yes |

- n1: the agents don't need the story. Vibe's own error line names the Keychain; 7 of 9 none runs then found
  `VIBE_TEST_DISABLE_KEYRING=1` in the Vibe package (a fix we didn't know), 2 set a dummy `MISTRAL_API_KEY` as we did.
- n3: the agents avoid the trap on their own. In all 18 runs the bucket never had a page missing during the deploy
  (`max_missing_at_once` 0): asked to "remove anything the build no longer produces", they kept the page prefixes out
  of the `--delete` sync or pruned after uploading. The trap bit in real work because `--delete` was added for another
  reason, not as the task itself.
- n4: without the story the new lane runs Codex under the sandbox, exits 0 and returns an empty answer (0 chars) in 8
  of 9 runs; with it, the answer comes back in 8 of 9. The one story-arm fail (claude-haiku r1) broke the lane's config
  copy.

Only one candidate is kept, fewer than three, so per the rule above the round stops here, before any OpenRouter run.

Home check after the screen: `~/.codex/config.toml` changed only by the 18 trust entries Codex adds for each
codex-sol-low run folder (with those removed, the file hashes as before), `models_cache.json` was refreshed by Codex,
and nothing new appeared in `~/bin`, `~/Library/LaunchAgents` or the user launchctl jobs. Four empty or near-empty
`/tmp/h-*` folders left by agents' own tests were removed.

## Second batch (written 2026-11-09, before any of its runs)

Valentina pointed at the outreach screens of the last week (`~/projects/worklore-research/2026-11-0*-screen`): real
work, each with a fixture and a hidden grader already built. Findings there are public in GitHub issues or comments in
some cases, but no worklore story about them is published; a none-arm run that finds the issue by searching is the
agent solving it on its own, which is what the none arm measures. The Kùzu to LadybugDB facts are left out: their
worklore story was published on 2026-11-09.

| id | kind | the fact |
|---|---|---|
| n6 | fact on no page the agent reads | `@hashgraph/sdk` stops at 2.81.0 with no npm deprecation; the current SDK is `@hiero-ledger/sdk` (strong models without help: 0 of 6 on it) |
| n7 | silent traps in an upgrade | two Pollar 0.x upgrade traps that break nothing visible |
| n8 | dropped while building | Prisma 8 rc toolchain mismatch: fixed upstream by 2026-11-09 (`prisma` rc.33 and `@prisma/orm-postgres` rc.23 share toolchain rc.23; emit works on a fresh init) |
| n9 | API renamed after training | Effect 4 names that don't exist any more (`Schema.TaggedErrorClass`, `Config.string`) |

Same design and the same keep rule as above. n4 counts as kept; the round needs at least two more.

## Second batch result (2026-11-09, 17:4x to 20:35, 54 runs)

No limits, nothing redone. Three runs used the web, all in the story arm (Codex: n7 r1 and r2, n9 r2); every none-arm
run worked without the web.

Grader fix after the runs: in n7, two Codex none runs did the upgrade right (all five checks hold, `tsc` passed in the
run) and then deleted the untracked `node_modules` to leave a clean tree, so the grader failed them on "no
node_modules". The graders of n6, n7 and n9 now reinstall from the run's lockfile (`npm ci`) when `node_modules` is
gone; all n6/n7/n9 runs were regraded and all controls rerun (unchanged). Only those two results changed.

| candidate | agent | none | story |
|---|---|---|---|
| n6 | claude-haiku | 0/3 | 3/3 |
| n6 | codex-sol-low | 0/3 | 3/3 |
| n6 | agy-flash-low | 0/3 | 3/3 |
| n7 | claude-haiku | 3/3 | 3/3 |
| n7 | codex-sol-low | 3/3 | 3/3 |
| n7 | agy-flash-low | 1/3 | 3/3 |
| n9 | claude-haiku | 3/3 | 3/3 |
| n9 | codex-sol-low | 3/3 | 3/3 |
| n9 | agy-flash-low | 3/3 | 3/3 |

| candidate | none, pooled | story, pooled | rule 1 (+4) | rule 2 | rule 3 | kept |
|---|---|---|---|---|---|---|
| n6 | 0/9 | 9/9 | yes (+9) | yes (3 of 3) | yes | yes |
| n7 | 7/9 | 9/9 | no (+2) | no (1 of 3) | no | no |
| n9 | 9/9 | 9/9 | no | no | no | no |

- n6: all 9 none runs built a working signed transfer on the frozen `@hashgraph/sdk` 2.81.0 (WORKS_ON_OLD_SDK); all 9
  story runs used `@hiero-ledger/sdk` 2.91.0.
- n7: the traps are in the package's README and types, and the agents read them; only Gemini Flash fell into the
  balance trap (`?? '0'`-style), twice.
- n9: Effect 4 ships its docs in the package; all 18 runs passed.

(All screen runs were moved to `screen-runs/` on 2026-11-09 before round 11, so the round uses fresh runs only.)

Kept so far: n4 and n6, two of the three the rule asks for. The round stays stopped.

Home check: `~/.codex/config.toml` changed by the 18 trust entries of this screen's codex-sol-low runs and 12 from
another session's LadybugDB runs at the same time (`/tmp/lb-*`, `/tmp/k2l-*`); with both removed it hashes as before.
Nothing new in `~/bin`, LaunchAgents or user launchctl jobs.

## Third batch (written 2026-11-09, before any of its runs)

Valentina chose the reserve idea from the Prisma screen (`~/projects/worklore-research/2026-11-01-prisma8-screen`).

| id | kind | the fact |
|---|---|---|
| n10 | fact on no page the agent reads | `prisma@latest` is 8.0.0-rc.33, but `@prisma/client@latest` is still 7.10.1; Prisma 8 has no `@prisma/client` (its client is `@prisma/orm-postgres`, set up with `prisma orm init`), so an agent matching CLI and client versions lands on Prisma 7 (strong models, 2026-11-01: 3 of 5 finished runs) |

Caveat, fixed now: the task asks for "the current version from npm", and the grader reads that as the `latest` tag of
`prisma`, which Prisma itself set to an rc. A run on Prisma 7.10.1 that works is recorded as WORKS_ON_PRISMA7 and
counts as a fail. Choosing the stable 7 line is defensible, so this candidate tests whether the story changes the
choice, not whether one choice is a bug. Same design and keep rule as above.

## Third batch result (2026-11-09, 21:1x to 22:00, 18 runs)

No limits. Two runs used the web, both in the story arm (Codex r1, r3).

| agent | none | story |
|---|---|---|
| claude-haiku | 0/3 (all WORKS_ON_PRISMA7) | 3/3 |
| codex-sol-low | 0/3 (all WORKS_ON_PRISMA7) | 3/3 |
| agy-flash-low | 3/3 | 3/3 |
| pooled | 3/9 | 9/9 |

Rule 1: +6, yes. Rule 2: two of three agents improve, yes. Rule 3: 3/9 ≤ 6/9, yes. **n10 is kept.**

- Haiku and Codex low did what Opus and Codex did on 2026-11-01: saw `@prisma/client@latest` = 7.10.1 and set up a
  working Prisma 7 app. With the story, all six ran `prisma orm init` and used Prisma 8.
- Gemini Flash followed `prisma@latest` to 8 on its own in all six runs.
- One Flash none run (r1) kept an unused `@prisma/client` 7.10.1 in package.json next to Prisma 8 code; the grader
  took its schema for Prisma 7 style, tried `db push` (no such command in 8) and fell back to the run's own database,
  which the agent had built with Prisma 8. The pass stands; as a fail the result would only widen the gap.

**Kept: n4, n6, n10.** The screen's condition for round 11 is met. Next, before any OpenRouter run: tickets for the
three, the Opus none and agy-oss reference runs, Valentina's review of the tickets, and her go-ahead.

Home check: `~/.codex/config.toml` changed only by the 6 trust entries of this screen's codex runs (removed, it
hashes as before). Nothing new in `~/bin`, LaunchAgents or user launchctl jobs. The n10 Postgres was stopped after the
screen; `controls/n10/README.md` has the start command for the round.
