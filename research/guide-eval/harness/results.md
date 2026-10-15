# Harness experiment: same model, two agent harnesses

Date: 2026-10-04. Question: with the model held constant, does the agent harness (Claude Code vs Antigravity) change the results of reproducing a worklore story?

24 runs. All exited with code 0, none hit the 15-minute timeout, and none failed on auth or quota.
- Sonnet 4.6: 2 stories × 2 arms (WITH guide / WITHOUT) × 2 harnesses × 2 repeats = 16 runs.
- Opus 4.6 (the optional second pair): 2 × 2 × 2 × 1 repeat = 8 runs.

## Setup

| | Claude Code ("cc") | Antigravity ("agy") |
|---|---|---|
| version | 2.1.285 | agy 1.2.16 |
| Sonnet | `--model claude-sonnet-4-6` (init event confirms `claude-sonnet-4-6`) | `--model claude-sonnet-4-6` (listed as "Claude Sonnet 4.6 (Thinking)") |
| Opus | `--model claude-opus-4-6` (confirmed by a trivial run) | `--model claude-opus-4-6-thinking` |
| flags | `-p … --dangerously-skip-permissions --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands --setting-sources project,local --settings '{"disableAllHooks":true}' --output-format stream-json --verbose` | `-p … --dangerously-skip-permissions --add-dir <workdir> --disable-slash-commands --output-format stream-json` |
| MCP / skills / hooks | none (init event shows `mcp_servers: []`, `skills: []`) | `agy mcp list` reports no MCP servers and `agy plugin list` no plugins. Its built-in tools and built-in skills docs are still present (see Surprises). |

- WORKLORE_TOKEN, WORKLORE_API and GEMINI_API_KEY were unset in every agent's environment.
- Fixtures, prompts and the shared ground-rules line are the same as in the 2026-10-03 experiment (`../prompts`, `../fixtures`).
- WITH arm: the task, then "Follow this guide:", then the story markdown, then the same ground-rules line as the WITHOUT arm.

**The stories differ from the first experiment.** Both were edited on 2026-10-04, and the WITH arm used the current text from `https://worklore.dev/s/<slug>.md` (copies in `stories/`):
- Story 1 (skill-xray) now fetches a pinned commit (`718c302…`) into a `mktemp -d` folder and checks its sha256. It also adds "Run the scanner even when the target looks small enough to read by hand".
- Story 3 (author-local dates) now says that deriving the local date from the client tz is fine: keep existing callers working, and never fall back to the UTC date. Its Verify adds two checks: a reader in a third timezone sees the same dates, and an existing caller that sends no date still gets the author's local date.

**Isolation (lessons from the first run, applied):**
- Each run worked in a fresh `mktemp -d /tmp/h-XXXXXX`. The path contains nothing named worklore, eval or story.
- The fixture was copied in and `git init`'d. No prompt file or grader sat in the workdir.
- After each run, the workdir was copied to the results tree and deleted from /tmp.
- Graders and other runs' results stayed in the session scratchpad, never next to the workdir.
- Four lanes ran in parallel (cc-sonnet, agy-sonnet, cc-opus, agy-opus), so up to 3 sibling `/tmp/h-*` dirs (fixture copies only) existed at a time. No agent listed or read them (checked from the tool-call logs).

**Graders:**
- Story 1: the grader is unchanged in logic. It now also records `pinned_commit_used`, `hash_checked` and `scan_py_in_workdir`.
- Story 3 has a new grader (`graders/grade_s3.py`). PASS = a + b + c + d:
  - (c) readers in Europe/Berlin and Pacific/Auckland see 2026-10-02 for both posts;
  - (d) `publish(entry, client_tz, now=)` with no date gives the author's local date.
- The old grader (`graders/grade_s3_old.py`, PASS = a + b) was also run on every s3 run, for comparability.

**Controls** (`controls/`):
- Both graders fail the unmodified fixtures.
- The first experiment's reference fix passes both graders.
- Two negative controls pass the old grader and fail the new one, as intended: convert to the viewer's zone (fails c), and fall back to UTC when no date is sent (fails d).
- The pinned scanner verifies against its sha256 and gives T4 for fetch-helper and T0 for tone-guide.

## Results

### Sonnet 4.6, story 1 (skill-xray; Verify = the real scanner gives T4 / T0)

| arm | harness | rep | tiers (fetch / tone) | scanner fetched | pinned + hash checked | scanner run | PASS | time | tool calls |
|---|---|---|---|---|---|---|---|---|---|
| without | agy | 1 | own scale ("Active/Execution" / "Passive/Advisory") | n | - | n | fail | 35s | 5 |
| without | agy | 2 | own scale ("Active (tool-augmented)" / "Passive (knowledge-only)") | n | - | n | fail | 32s | 5 |
| without | cc | 1 | own scale ("Tier 3 — Elevated" / "Tier 0 — Passive") | n | - | n | fail | 40s | 8 |
| without | cc | 2 | own scale ("High" / "Low") | n | - | n | fail | 24s | 5 |
| with | agy | 1 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 53s | 8 |
| with | agy | 2 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 50s | 9 |
| with | cc | 1 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 34s | 9 |
| with | cc | 2 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 29s | 5 |

### Sonnet 4.6, story 3 (author-local dates)

a = each author sees their own local date; b = feed order matches submission order; c = a reader in a third zone sees the same dates (new); d = an existing caller that sends no date still gets the author's local date (new).

| arm | harness | rep | a | b | c | d | PASS new Verify | PASS old Verify | tests added | time | tool calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| without | agy | 1 | Y | Y | Y | Y | **PASS** | **PASS** | 0 | 50s | 5 |
| without | agy | 2 | Y | n | Y | Y | fail | fail | 0 | 48s | 5 |
| without | cc | 1 | Y | n | Y | Y | fail | fail | 2 | 94s | 8 |
| without | cc | 2 | Y | n | Y | Y | fail | fail | 3 | 116s | 11 |
| with | agy | 1 | Y | Y | Y | Y | **PASS** | **PASS** | 7 | 71s | 7 |
| with | agy | 2 | Y | Y | Y | Y | **PASS** | **PASS** | 6 | 77s | 7 |
| with | cc | 1 | Y | Y | Y | Y | **PASS** | **PASS** | 5 | 98s | 7 |
| with | cc | 2 | Y | Y | Y | Y | **PASS** | **PASS** | 5 | 83s | 7 |

### Opus 4.6, story 1

| arm | harness | tiers (fetch / tone) | scanner fetched | pinned + hash checked | scanner run | PASS | time | tool calls |
|---|---|---|---|---|---|---|---|---|
| without | agy | own scale ("active" / "passive") | n | - | n | fail | 82s | 14 |
| without | cc | own scale ("autonomous" / "prompt-only") | n | - | n | fail | 32s | 5 |
| with | agy | T4 / T0 | Y | pinned + hash | Y | **PASS** | 50s | 9 |
| with | cc | T4 / T0 | Y | pinned + hash | Y | **PASS** | 44s | 10 |

### Opus 4.6, story 3

| arm | harness | a | b | c | d | PASS new | PASS old | tests added | time | tool calls |
|---|---|---|---|---|---|---|---|---|---|---|
| without | agy | Y | Y | Y | Y | **PASS** | **PASS** | 0 | 99s | 10 |
| without | cc | Y | n | Y | Y | fail | fail | 2 | 98s | 9 |
| with | agy | Y | Y | Y | Y | **PASS** | **PASS** | 6 | 76s | 7 |
| with | cc | Y | Y | Y | Y | **PASS** | **PASS** | 6 | 78s | 9 |

### First experiment's Claude Code + Opus 5.5 rows (2026-10-03, *old* story text), for comparison

| story | arm | old Verify | re-graded with the new s3 grader | time | tool calls |
|---|---|---|---|---|---|
| s1 | without | fail (own scale) | n/a | 24s | 3 |
| s1 | with | fail: tiers right, but it decided not to fetch the scanner ("3 files, read by hand") | n/a | 28s | 3 |
| s3 | without | **PASS** (fixed the feed tiebreak by itself: sort by `created_at`) | **PASS** (a b c d all Y) | 52s | 4 |
| s3 | with | **PASS** | **PASS** (a b c d all Y) | 51s | 4 |

## Analysis

**On the Verify outcomes the harness made almost no difference with the model fixed.**

- Results by arm:
  - WITH: 12 of 12 runs passed, across both harnesses, both models, both stories and both repeats.
  - WITHOUT, story 1: 6 of 6 failed in both harnesses. Every run invented its own scale.
  - WITHOUT, story 3: this is the only cell where the harnesses split.
- Story 1 WITH is identical across harnesses, down to the commands:
  - Every run fetched the pinned commit into `mktemp -d`, checked the hash, and ran `python3 "$tmp/scan.py"` on each folder.
  - The Sonnet runs ran the guide's block verbatim (`sha256sum -c`). Both Opus runs, in *both* harnesses, split it into steps and swapped in `shasum -a 256 -c`, the macOS tool. That difference follows the model, not the harness.
  - No run dropped scan.py into the scanned folder, and no run executed `update.sh`.
- The story-1 edit fixed the "Claude decides not to fetch" problem, at least for 4.6 models. The new line "run the scanner even when the target looks small" was followed in both harnesses. The first experiment's Opus 5.5 skip came from a different model *and* the old text, so this run cannot say which of the two caused it.

**Story 3 WITHOUT: Antigravity passed 2 of 3, Claude Code 0 of 3. All failures are one check: (b) feed order.**

- The fixture's `feed()` sorts by `(date, author)`. That is a trap the task prompt never mentions, because it only says "the wrong date".
- Every cc WITHOUT run (Sonnet ×2, Opus ×1) fixed the date and left `feed()` untouched.
- agy-Sonnet r1 and agy-Opus noticed the trap and sorted by `created_at`. agy-Sonnet r2 did not.
- With n = 3 per side, this is not statistically meaningful (Fisher exact p ≈ 0.4). Treat it as a lead, not a finding.
- The first experiment's cc + Opus 5.5 *did* fix the tiebreak, so this is not a fixed Claude Code trait either.
- The new checks (c) and (d) never discriminated. Every 4.6 run, WITH or WITHOUT, in both harnesses, showed one date to every viewer and kept the `publish(entry, client_tz)` contract.
  - In the first experiment, three non-Claude agents converted to the viewer's zone (WITHOUT). Three WITH runs broke existing callers; one of those fell back to UTC.
  - So the story-3 edit closes a gap that Claude-family models did not fall into here. The edit's value is for other models; it cost nothing here.

**Where the harness did show up consistently (behaviour, not grades):**

1. **Writing tests unprompted (s3 WITHOUT): cc 3 of 3, agy 0 of 3.**
   - Claude Code added 2–3 regression tests in every WITHOUT run.
   - Antigravity changed only `journal.py` (8–10 added lines vs 18–25).
   - With the guide, both harnesses wrote 5–7 tests.
   - Same model, opposite default, consistent across repeats and both models. This is the clearest harness effect, plausibly from Claude Code's system prompt ("verify your work" / testing guidance).
   - It is not an Antigravity trait on its own: Gemini in agy did add tests in the first experiment. It is a harness × model interaction.
2. **Speed.**
   - cc was faster on story 1: 24–44s vs 32–82s; WITH 29–44s vs 50–53s.
   - cc was slower on story 3 WITHOUT: 94–116s vs 48–99s, because of the extra test-writing.
   - On story 3 WITH the two were similar: 78–98s vs 71–77s.
   - Both lanes ran concurrently on the same network, but each harness calls a different backend, so time is only a rough signal.
3. **Output volume.** On story 3, cc Sonnet emitted 6.0k–7.8k output tokens per run, agy Sonnet 2.0k–4.2k.
   - cc emits (empty-text) thinking blocks. agy reports `thinking_tokens: 0` on every run, even for models labelled "(Thinking)".
   - So the two harnesses may not run the model with the same reasoning configuration. See Caveats.
4. **Run-to-run determinism.** agy repeats were near-identical.
   - s1-agy-sonnet-without r1/r2: 5 tool calls each, 7352 vs 7454 input tokens. s3-agy-sonnet-with r1/r2: 7 calls each, same file set.
   - cc repeats varied more. One s1 WITHOUT run spawned two Explore subagents to read three tiny files (8 calls vs 5).
5. **Harness-native affordances.**
   - cc-Sonnet s1 WITH r1 loaded `WebFetch` via `ToolSearch` (a deferred tool) and then used `curl` as the guide said anyway.
   - cc-Sonnet s1 WITHOUT r1 used `Agent` (Explore subagents).
   - agy-Opus s1 WITHOUT went to Antigravity's own built-in skills docs to find out what a skill "tier" might mean (Surprises 1).
   - In the first experiment, agy-pro similarly grepped Antigravity's own transcript.
   - Antigravity seems to steer models toward its own installation as a reference source.

**What did not differ:**
- No run in either harness asked a question or stalled.
- None used a todo or planning tool, refused, or added a caution disclaimer.
- None executed `update.sh`, touched ~/projects, or looked at sibling run dirs or the scratchpad.
- Writes outside the workdir were limited to:
  - the scanner temp dir under `/var/folders/…/T/` (story-1 WITH, by design);
  - each harness's own session state (`~/.claude/projects/-private-tmp-h-*`, Antigravity's `~/.gemini`).

**Bottom line.**
- With the model fixed, the harness did not change whether a guide-following run passes. The guides are explicit enough that both harnesses execute them identically.
- The harness did change the defaults when there is no guide: whether the agent writes tests, how much it verifies, and (weakly) whether it spots an unmentioned adjacent bug.
- The cross-agent differences in the first experiment are mostly model differences, plus the story text that has since been edited, not harness differences. The one exception is Claude Code's testing default.

## Surprises

1. **agy + Opus 4.6, s1 WITHOUT, read Antigravity's own built-in skills docs.**
   - It ran `ls` and read `~/.gemini/antigravity-cli/builtin/skills/agy-customizations/{SKILL.md,docs/skills.md,docs/plugins.md}` and `antigravity_guide/SKILL.md`, looking for a definition of skill capability tiers.
   - This is read-only and harmless, but it means the harness's local docs are part of the context the model reasons from. It made this the slowest story-1 run (82s, 14 calls).
2. **Every story-1 WITH run reproduced the new pinned + hashed fetch.**
   - In the first experiment, every fetch was an unpinned `main`.
   - The story edit propagated perfectly. Nobody commented on it, and nobody skipped the hash check.
3. **The story-3 trap now separates the arms more than before.**
   - In the first experiment, every WITHOUT run caught the `(date, author)` tiebreak.
   - Here 4 of 6 4.6-model WITHOUT runs missed it. The guide's Verify ("feed order must match submission order") is what makes WITH runs catch it.

## Caveats

- **n is tiny.** 2 repeats for Sonnet and 1 for Opus. Only one cell (s3 WITHOUT) shows a pass/fail split, and it is not significant. The behavioural differences (tests, tokens, determinism) are consistent across all repeats, but still only 3 vs 3.
- **"Same model" is nominal.**
  - Both harnesses report the model id `claude-sonnet-4-6` / Opus 4.6.
  - agy calls its variants "(Thinking)" yet reports zero thinking tokens, while cc emits thinking blocks.
  - The system prompt, tool set and reasoning budget all differ by harness. That is the point of the experiment, but it means "harness" bundles all three.
  - agy serves Claude through Google's backend, cc through Anthropic's API, so time and determinism may partly reflect the serving stack.
- **The stories changed between experiments.** The first experiment's Opus 5.5 rows used the old text. Opus 5.5 also differs as a model, so neither comparison isolates one variable.
- **Story-3 "b" is not part of the task prompt.** In the WITHOUT arm, missing the feed tiebreak is arguably out of scope, not an error.
- **The (c)/(d) checks did not discriminate** among Claude-family runs. They were validated only on synthetic negative controls.
- **Run conditions.** Lanes ran in parallel, so up to three sibling `/tmp/h-*` workdirs (fixture copies) were visible to `ls /tmp`. No agent looked. Parallel load may affect wall time.
- **The guide was inline in the prompt.** "Read the guide fully" cannot be observed directly. Evidence that it was followed end-to-end: all WITH runs executed the late-section steps (s1: hash check, scanner on both folders; s3: `received_at`, third-zone tests in all 6 WITH runs).

## Files

- `run.sh`, `lane.sh`: the harness.
- `behave.py`: extracts behaviour from the logs.
- `aggregate.py`, `make_table.py`: build `results.json` and `table.md`.
- `graders/`: `grade_s1.py`, `grade_s3.py` (new Verify), `grade_s3_old.py` (old Verify) and `common.py`.
- `prompts/`, `stories/` (the 2026-10-04 story text used in the WITH arm), `controls/` (grader controls and the pinned scanner).
- `runs/<story>-<harness>-<model>-<arm>-r<rep>/`:
  - `prompt.txt`, `agent.log` (structured stream), `agent.err`, `diff.patch`;
  - `grade.json`, `grade_old.json` (s3), `behave.json`, `meta.json`, `workdir`.
- `prior/`: the first experiment's Claude Code + Opus 5.5 s1/s3 runs, with `grade_new.json` (s3 re-graded with the new grader) and `behave.json`.
