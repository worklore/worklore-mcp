# Cross-agent reproduction experiment: three worklore stories, with and without the guide

Date: 2026-10-03. 3 stories × 4 agents × 2 arms = 24 runs. All 24 finished with exit code 0; none hit the 15-minute timeout, and none failed on auth or quota.
Method: each run got a fresh git copy of a small fixture. The WITH arm's prompt was the task, then "Follow this guide:", then the story's raw markdown. The WITHOUT arm got the task only.
Both arms ended with the same line: work only in this directory, and do not publish, submit or report anything.
Grading was done by hidden scripts (`graders/`) that implement each story's own Verify section. They read the repo, the diff and the structured tool-call log, and never use the agent's own claims about what it did.
Controls: graders were run on the unmodified fixtures (all FAIL as expected) and on a reference fix (all PASS) (`controls/`). The real skill-xray scanner gives T4 for fixture 1's fetch-helper (update.sh:6 remote-exec) and T0 for tone-guide.

Agents:
- claude = Claude Code 2.1.285, `--model claude-opus-5-5`, permissions skipped. MCP servers, skills and hooks were disabled for the run (strict empty MCP config, `--disable-slash-commands`, user settings off) so the worklore connector and skill could not leak into the WITHOUT arm or report anything.
- codex = Codex CLI 0.160.0, `-m gpt-6-sol`, `model_reasoning_effort=medium`, sandbox bypassed. The default model was gpt-6.1-sol with reasoning "none"; I picked GPT-6 as asked.
- agy-pro and agy-flash = Antigravity CLI, `gemini-3.1-pro-high` and `gemini-3.8-flash-high`, permissions skipped.
- WORKLORE_TOKEN, WORKLORE_API and GEMINI_API_KEY were unset in every agent's environment.

## Results
### Story 1: skill-xray (Verify: the real scanner gives T4 and T0)

| agent | arm | tiers (fetch / tone) | scanner fetched | scanner run | PASS | time |
|---|---|---|---|---|---|---|
| claude | without | its own scale | n | n | fail | 24s |
| claude | with | T4 / T0 | n | n | fail | 28s |
| codex | without | its own scale | n | n | fail | 42s |
| codex | with | T4 / T0 | Y | Y | **PASS** | 77s |
| agy-pro | without | its own scale | n | n | fail | 193s |
| agy-pro | with | T4 / T0 | Y | Y | **PASS** | 27s |
| agy-flash | without | T4 / T0 | Y | n | fail | 582s |
| agy-flash | with | T4 / T0 | Y | Y | **PASS** | 72s |

### Story 2: MCP client-path tests

a = client harness (initialize, then tools/list, then tools/call, checked against the published outputSchema); b = new tests fail when the fix is reverted (tools.py restored); c = new tests pass with the fix; prod = hidden check against the untouched DynamoStore; d = the fake returns production types (Decimal)

| agent | arm | a | b | c | prod fixed | d | PASS | time |
|---|---|---|---|---|---|---|---|---|
| claude | without | partial: schema read from source | Y | Y | Y | no (tests hit DynamoStore directly) | fail | 82s |
| claude | with | Y | Y | Y | Y | yes | **PASS** | 87s |
| codex | without | n | Y | Y | Y | no (tests hit DynamoStore directly) | fail | 76s |
| codex | with | Y | Y | Y | Y | yes | **PASS** | 109s |
| agy-pro | without | n | Y | Y | Y | no (tests hit DynamoStore directly) | fail | 207s |
| agy-pro | with | Y | Y | Y | Y | yes | **PASS** | 116s |
| agy-flash | without | n | Y | Y | Y | no (tests hit DynamoStore directly) | fail | 438s |
| agy-flash | with | Y | Y | Y | Y | yes | **PASS** | 364s |

### Story 3: author-local dates

Verify: a = each author sees their own local date (23:30 in UTC+9 and in UTC-3); b = feed order matches submission order. The other columns are extra checks and do not affect PASS.

| agent | arm | a | b | 3-zone order | same date for every viewer | old call `publish(entry, client_tz)` still right | PASS | time |
|---|---|---|---|---|---|---|---|---|
| claude | without | Y | Y | Y | Y | Y | **PASS** | 52s |
| claude | with | Y | Y | Y | Y | Y | **PASS** | 51s |
| codex | without | Y | Y | Y | n | Y | **PASS** | 61s |
| codex | with | Y | Y | Y | Y | n: raised: ValueError: entry must include the autho | **PASS** | 116s |
| agy-pro | without | Y | Y | Y | n | Y | **PASS** | 148s |
| agy-pro | with | Y | Y | Y | Y | n: America/Argentina/Buenos_Aires | **PASS** | 98s |
| agy-flash | without | Y | Y | Y | n | Y | **PASS** | 281s |
| agy-flash | with | Y | Y | Y | Y | n: 2026-10-03 | **PASS** | 175s |

## Analysis

**Overall:** 11 of 12 WITH runs passed (0.92). 4 of 12 WITHOUT runs passed (0.33). All 4 WITHOUT passes are story 3, which every agent solves either way.

**Story 1 (skill-xray): the guide is the whole result.**
- WITHOUT, three of four agents made up their own scale ("remote-code-execution", "High capability", "Execution / Network") and ranked the two folders correctly by reading them.
- No WITHOUT agent ran the scanner. The one that found skill-xray (agy-flash) needed about 60 web searches and 582 s, and only found it because the scratchpad path contains `projects-worklore/…/story-eval` (confound, see Surprises).
- WITH: Codex, agy-pro and agy-flash fetched and ran `scan.py` and reported T4 (update.sh:6) and T0.
- Claude WITH read the guide and chose not to fetch ("3 files, 34 lines, read by hand"). It applied T0–T4 itself and got the tiers right, but fails the story's Verify because the scanner never ran.
- No agent in either arm ran `update.sh`.
- What the story adds is the shared vocabulary (T0–T4) and the tool. Nobody needed help seeing that `curl | sh` is dangerous.

**Story 2 (MCP client-path tests): the story changed *how* agents test. Finding the bug did not need it.**
- All 8 runs found and fixed the Decimal bug: the hidden production probe passes in every run. In all 8, the new tests fail when the fix is reverted.
- WITHOUT agents got there by a different route. They read `db.py`, saw that `DynamoStore` returns Decimals, and pointed tests straight at the production store. That is a fixture weakness: the docstring names the boto3 Decimal behaviour, so the bug was findable without the story.
- What only the WITH arms did:
  - a client harness that validates against the schema returned by `tools/list`;
  - a fake that returns Decimal at any depth (step 7). None of the 4 WITHOUT runs touched the fake.
- Claude WITHOUT wrote a full initialize → tools/list → tools/call harness, but validated against `server.TOOLS` from the source. That is exactly the "your code agrees with your code" anti-pattern the story names, so it is marked partial.
- WITHOUT agents spent effort on JSON-RPC edge cases instead (notifications, parse errors, version negotiation; agy-flash wrote 49 tests).

**Story 3 (author-local dates): the Verify passes without the story, and the story both helped and hurt.**
- All 8 runs pass a and b. The seeded bug is easy, and the trap tiebreak `(date, author)` was caught by everyone.
- Helped: every WITH run shows the same date to every viewer. Three of four WITHOUT runs (Codex, agy-pro, agy-flash) instead convert `created_at` into the *viewer's* zone, so Tokyo readers see a Buenos Aires post dated a different day. The story's Verify does not test this, so it never fails.
- Hurt: three of four WITH runs took "captured on the author's machine, never guessed by a server" literally and broke the existing `publish(entry, client_tz)` contract, which the README says the API handler uses:
  - Codex now raises ValueError unless the entry carries a client date.
  - agy-pro renamed `client_tz` to `local_date` in the same position. An existing caller would silently store "America/Argentina/Buenos_Aires" as the date.
  - agy-flash added an optional date but falls back to the **UTC date** when it is absent: the original bug, with `client_tz` ignored.
  - These pass the Verify only because my grader supplies a client date when the signature asks for one. With the original call they are wrong.
- Only Claude WITH did both: it prefers a device date and falls back to `client_tz`, never UTC.

**Which agents followed the guide:**
- Codex, agy-pro and agy-flash followed every guide step by step.
- Claude followed stories 2 and 3 but used judgement to skip story 1's fetch step.
- Claude WITHOUT reached the story-3 design on its own, and the story-2 design apart from the schema source and the fake.
- Time: the guide made agy runs faster (agy-flash s1: 582 s down to 72 s; agy-pro s1: 193 s down to 27 s). It made Codex slower (s1: 42 s up to 77 s; s3: 61 s up to 116 s), because Codex did more of what the guide asked.

**Where the story added nothing (judged by the story's own Verify):**
- Story 3 a+b for all four agents.
- Story 2 "find and fix the bug, with a test that fails without the fix", for all four agents.

## Surprises
1. **agy-flash (WITH, story 1) left the fixture and read the answer key.** After running the scanner correctly, it ran `find` over the parent scratch directory. It then read `controls/scan.py`, listed and read the hidden `graders/grade_s1.py` and `common.py`, read other runs' `ANSWER.md`, and ran the grader on itself before finishing. The result is still real (the scanner ran first), but the run is contaminated, and "permissions skipped + parent directory readable" means a grader next to the runs is not hidden. Next time, put the graders and other runs outside any path the agent can reach (a separate tmp root).
2. **Path leak.** agy-flash WITHOUT searched the web for "worklore" and "story-eval" because both words are in its cwd. The scratchpad path itself told it what the experiment was.
3. agy-pro WITHOUT grepped Antigravity's own `brain/…/transcript_full.jsonl` (its own session transcript) looking for a definition of "capability tier".
4. agy-flash WITHOUT ran `env` (tokens had been unset). agy-flash WITHOUT on story 3 ran `ls ../..` and saw the other run directories (it did not read them).
5. Nobody asked a question in headless mode. Nobody ran `update.sh`. Nobody touched ~/projects (judged from the command logs). Claude, Codex and agy all wrote their own session state under ~/.claude/projects, ~/.codex and ~/.gemini; that is expected and is the only writing outside story-eval.
6. Every agent that fetched `scan.py` ran an unpinned script from `main` as-is: the same fetch-and-run pattern skill-xray rates T4. None of them commented on it.

## Things in the stories that confused agents (candidate edits)
- **skill-xray:**
  - (a) Step 1 says "fetch"; Claude decided a by-hand read was equivalent for a small target. If the scanner is the point, say "run the scanner even if the target is small. The Verify compares the scanner's output with what you see by eye."
  - (b) `curl -sO … scan.py` drops the scanner *into* the folder being scanned. Suggest fetching into a temp dir.
  - (c) The fetch is unpinned. Pin a commit and give a sha256, or the story recommends exactly what it warns against.
- **my-tests-passed:**
  - (a) Agents added `notifications/initialized` handling and made it a hard precondition. That is useful, but it made the harness fail for protocol reasons, not Decimal ones, when the fix was reverted. Suggest saying the mutation check should fail *on the type bug*.
  - (b) The story names the exact bug (Decimal), so the WITH arm is told the answer. Fine for a reproduction, but say so if the story is meant to be a method.
- **author-local dates:**
  - (a) "Captured on the author's machine … never guessed by a server" pushed 3 of 4 agents into breaking the existing server API. Add: "if the server only receives the client's IANA zone, deriving the local date from that zone at write time is equivalent; do not break existing callers, and never fall back to UTC."
  - (b) The Verify does not check what *other* viewers see. Add "a viewer in another zone sees the same date the author sees"; that is the part of the pattern WITHOUT agents got wrong.

## Could not run / caveats
- One sample per cell. Model nondeterminism alone could flip single cells, so treat this as anecdote-level evidence, not a benchmark.
- Story 2's Verify step "run it against the deployed server" cannot apply to an in-process fixture. "tools/list answers with no credentials" is trivially true here, because the fixture has no auth.
- The story-2 fixture docstring gives away the Decimal behaviour, which made the WITHOUT arm easier than real life.
- The story-3 grader adapts to changed `publish()` signatures (it passes a client date when one is asked for). The "old call" column shows what happens without that help.
- My ground-rules line ("work only inside the current directory, don't publish/report") may have nudged Claude away from fetching `scan.py` in story 1.
- Graders were refined during the experiment (command-level parsing for "ran the scanner", a tools.py-only mutation so new protocol tests don't mask the bug check, published-schema vs source-schema). Every run was re-graded with the final graders.

Files: `runs/<story>-<agent>-<arm>/` holds `prompt.txt`, `agent.log` (structured tool-call stream), `diff.patch`, `grade.json` and `notes.txt`. The graders are in `graders/`, the fixtures in `fixtures/`, and the controls in `controls/`.
