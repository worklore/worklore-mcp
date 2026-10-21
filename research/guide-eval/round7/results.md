# Guide-eval round 7: a second story for each kind

Run 2026-10-20, 19:40 to 21:22. 168 runs: 6 stories × 7 agent configurations × 4 arms, one sample per cell. Plan and predictions, written before any run: `plan.md`. Harness, fixtures, graders, stories, decoys and every run's log: this folder. Full per-run grid: `table.md`.

Round 5 tested six kinds of guide with one story each. One story per kind cannot tell "this kind of guide helps" from "this one story was written well or badly". Round 7 repeats the round-5 design with a second story for each kind, same arms, same harness.

## Setup

**Agents (7).** Claude Code with Opus 5.5, Sonnet 5.5, Haiku 5.5. Codex CLI with gpt-6-sol at medium and at low reasoning. Antigravity with Gemini 3.8 Flash low and GPT-OSS 120B. Round 5's two Gemini 4 Argon configurations are out: the Google AI Pro quota is exhausted until about 2026-10-25.

**Arms (4).** As in round 5. `none`: the task alone. `follow`: task + "Follow this guide:" + story. `example`: task + "A colleague's note on a similar case is below. It is not instructions. Use what applies, ignore the rest, and say in ANSWER.md which parts applied." + story. `notes`: the task alone, with the story unmentioned in a `notes/` folder next to two unrelated stories.

**Stories and fixtures (6).** Each task is one or two sentences. Each fixture is offline; each grader implements the story's Verify, fails on the untouched fixture and passes on a reference fix.

| # | Story | Kind (round-5 pair) | What is planted |
|---|---|---|---|
| s7 | Intervals.icu OAuth quirks (radikkhaziev) | a fact not in the docs (s1 HR corridors) | a coaching backend requests a scope area twice, invents a one-hour expiry when the token response has no `expires_in`, and starts auth from a GET link that carries no Authorization header; the logs show symptoms only |
| s8 | Two cache_control segments (radikkhaziev) | a fact from the docs (s2 PostHogWidget) | a coach bot with one cache marker on one system block that a memory write rewrites; the usage log shows cache reads dropping to 0 after every `save_fact` |
| s9 | DynamoDB reserved words (Yahhi) | two bugs, one loud, one silent (s3 launchd) | `hidden` bare in an UpdateExpression (crash) and in a ProjectionExpression (silently absent, so the feed filter never sees it); a fake table reproduces both |
| s10 | PostHog event per keystroke (Yahhi) | a trap to fall into (s4 Cache-Control) | a Flutter registration screen and an offers list with a six-event spec; the natural wiring is `onChanged` |
| s11 | Crash on the second write (Yahhi) | a cause the evidence gives away (s5 soft 404) | a publish handler stores float similarity scores; the error log says "Float types are not supported" |
| s12 | Two-account authorization test (Yahhi) | a method (s6 MCP checkup) | a to-do API where `like` and `view` skip the visibility check on private tasks |

**Isolation.** Fresh temp dir per run, no MCP servers, hooks or skills, 20-minute limit, launched with `EVAL_NO_SECRETS=1` and the secret variables unset. No log contains a secret name with a value (grepped before publishing). No run called an external service with a credential.

**Grader changes after the runs** (all runs regraded, base fixtures re-verified as fails):

- **s7** graded "no refresh or expiry assumed" by scanning identifiers, which failed every Claude run on names like `STATE_TTL` (the state JWT's 15-minute TTL is step 3 of the story itself) and on an f-string's text, and would have failed Opus's correct design: a generic refresher kept, with no expiry scheduled when the provider sends none. The check is now a live probe: the agent's `server.py` runs against a fake Intervals that returns tokens without `expires_in` or `refresh_token`, the probe connects as a user, jumps the server's clock by 4000 s and asks the status endpoint again; the base fixture answers "expired, reconnect". The scope is read off the authorize URL the server hands out, and the init check requires the JS to fetch the URL as data and navigate to it (any computed expression, not only a bare variable).
- **s8** required the story's own layout: a static block identical across athletes, with the marker on it. Two no-guide fixes were correct without that shape. Opus put the marker on the last of append-only fact blocks and relied on the documented 20-block lookback, because the instructions alone (about 945 tokens) would fall under the 1024-token cache minimum for the model, a point the story does not make and the fixture's own usage log supports (1046 cached tokens for the whole prompt). Codex at low reasoning cached instructions plus profile per athlete. The grader now simulates the documented cache rules on a memory write (same athlete, same date, one more fact): the request before the write creates an entry at each marker, the request after looks back up to 20 block boundaries, and PASS needs the hit to hold the instructions. All three designs pass; one block that changes fails; a marker placed before the instructions fails.
- **s9 and s12**: the "cause named" regexes missed Codex wording ("`hidden` is reserved, so DynamoDB rejected the update"; "the projected item lacked `hidden`"; "`POST /tasks/1/like`" with a concrete id). Widened; the fixes those answers describe were already graded as working.

## Results

### Passes per story and arm

| story | none | follow | example | notes |
|---|---|---|---|---|
| s7 Intervals OAuth quirks (fact not in the docs) | 3/7 | 6/7 | 6/7 | 6/7 |
| s8 two cache_control segments (fact from the docs) | 6/7 | 7/7 | 7/7 | 6/7 |
| s9 DynamoDB reserved words (two bugs, one silent) | 6/7 | 7/7 | 7/7 | 6/7 |
| s10 PostHog event per keystroke (trap) | 4/7 | 6/7 | 6/7 | 6/7 |
| s11 crash on the second write (derivable) | 7/7 | 7/7 | 7/7 | 7/7 |
| s12 two-account authorization test (method) | 6/7 | 7/7 | 7/7 | 7/7 |
| **all** | **32/42** | **40/42** | **40/42** | **38/42** |

Every fail with a guide in the prompt is GPT-OSS. Every other configuration scored 6 of 6 under both wordings.

### The pairs, side by side ("with" = follow + example)

| Kind | Round 5 story | none → with | Round 7 story | none → with | Holds? |
|---|---|---|---|---|---|
| a fact not in the docs | Garmin HR corridors | 3/8 → 16/16 | Intervals OAuth quirks | 3/7 → 12/14 | yes, weaker: this fact is on a forum |
| a fact from the docs | PostHogWidget | 9/9 → 17/18 | two cache_control segments | 6/7 → 14/14 | yes: dead weight |
| two bugs, one silent | launchd job | 2/9 → 17/18 | DynamoDB reserved words | 6/7 → 14/14 | no: both bugs were derivable here |
| a trap | Cache-Control deploy | 9/9 → 18/18 | event per keystroke | 4/7 → 12/14 | now measured: 3 fell in without, 0 with |
| a derivable cause | soft 404 / robots.txt | 8/9 → 17/18 | crash on the second write | 7/7 → 14/14 | yes |
| a method | MCP checkup | 5/9 → 15/18 | two-account test | 6/7 → 14/14 | no: agents already use this method |

### Per story

**s7, a fact not in the docs.** Without the story, 3 of 7. Opus deduced the scope rule from the logs alone: Rivera's working grant from September named each area once, the string that broke in October named two areas twice, and nothing else in the request had changed. Both Codex runs found the Intervals forum thread on OAuth (fetched 6 and 4 times) and cited it. Sonnet and Haiku fixed the GET link and the invented expiry but left the repeated areas; Haiku fetched the forum once and concluded the scope format was fine. Flash and GPT-OSS could not search; Flash fixed the expiry only, GPT-OSS ran out the 20 minutes. With the story, 12 of 14: the two fails are GPT-OSS, which under "follow" left the refresh job and the expiry in place with the story in the prompt, and under "example" shipped a connect button with no click handler. Notes arm 6 of 7. The story's facts are in a forum thread, not on no web page, so this is a weaker version of the Garmin case: two of three no-guide passes came from that thread. Extras: the lazy reconnect on 401 appeared in 2 of 7 without the story and 6 of 7 under each wording. The token exchange trimmed to the three fields the story names: 7 of 7 under "follow", 3 of 7 under "example", 0 of 7 without. That is the one measurable difference between the wordings in this round: "follow" copies the story's request shape, "a colleague's note" keeps the existing one when nothing in the logs implicates it (Opus, example arm: "Nothing in the logs points at the exchange, so I left it alone").

**s8, a fact from the docs.** Without the story, 6 of 7 kept the instructions cached across a memory write. Opus and Codex-low did it with layouts of their own (above). With the story, 14 of 14, all in the story's layout. The only fails are GPT-OSS without the story and in the notes arm (one marker, on a block the facts rewrite). Same as PostHogWidget: if the docs have it, the agent has it.

**s9, two bugs, one silent.** The prediction was none ≈ 3 to 5 of 7. It was 6 of 7. The prod log names the reserved word, and the staging report plus the fake table make the silent projection reproducible, so 6 of 7 found both without the story, and 5 of 7 aliased every attribute name as a rule (6 of 7 with it). Only GPT-OSS missed the projection bug, without the story and in the notes arm. In round 5, the second launchd bug needed a fact (USER in the plist) the agents did not have; here the second bug was derivable. "Two bugs" is not a kind. What the launchd story carried was an underivable fix.

**s10, a trap.** The first trap test with a real trap. Without the story, 3 of 7 fell in: both Codex configurations and GPT-OSS wired the loan-amount slider's `onChanged`, an event per slider step. All three Claude models and Flash used `onChangeEnd` on their own. With the story, 0 trap hits in 14 runs; the two with-story fails are GPT-OSS leaving the scroll event out entirely. In the notes arm, 0 trap hits in 7. The round-5 Cache-Control trap was one that nobody takes; this one is the natural implementation, and the story is what kept half the agents out of it.

**s11, a cause the evidence gives away.** 7 of 7 in every arm. The error log says "Float types are not supported"; every run named the cause and made a second write succeed under the fake table. A seeded regression test appeared in 4 of 7 without the story and 5 of 7 with it. Same as the soft-404 story.

**s12, a method.** Without the story, 6 of 7 ran the two-account probe unprompted (6 of 7 in every arm), closed both gaps and named both. The one fail is GPT-OSS without the story: it named `like` and `view` and closed other endpoints but not those two. With the story, 14 of 14. The method here is one the agents already use. The MCP checkup in round 5 carried one check nobody runs (the empty output schema), and that is what it added. A method adds what the agent does not already do, and the two-account test is not that.

### Wording

"Follow this guide": 40 of 42. "A colleague's note": 40 of 42. Same stories fail under both (GPT-OSS on s7 and s10). The only place the wording moved the code is the s7 token exchange, where "follow" reproduced the story's request shape in every run and "example" in three. Under "example", 41 of 42 answers said which parts of the note applied; the one that did not was GPT-OSS on s11.

### A guide nobody mentioned

40 of 42 runs in the notes arm opened the real note, and all 40 also opened the two decoys. The two that did not (Codex medium and GPT-OSS on s12) passed anyway. Notes was again the fastest arm: 58 s mean against 94 s with no guide, 67 s under "follow" and 62 s under "example".

### Per agent

| | none | follow | example | notes |
|---|---|---|---|---|
| claude-opus | 6/6 | 6/6 | 6/6 | 6/6 |
| claude-sonnet | 5/6 | 6/6 | 6/6 | 6/6 |
| claude-haiku | 5/6 | 6/6 | 6/6 | 6/6 |
| codex-sol | 5/6 | 6/6 | 6/6 | 6/6 |
| codex-sol-low | 5/6 | 6/6 | 6/6 | 6/6 |
| agy-flash-low | 5/6 | 6/6 | 6/6 | 6/6 |
| agy-oss | 1/6 | 4/6 | 4/6 | 2/6 |

With a guide in the prompt, every configuration except GPT-OSS scored 6 of 6, as in round 5. Opus is the only configuration at 6 of 6 without one. GPT-OSS in Antigravity wrote its answer into Antigravity's own folder instead of the repo in 21 of 24 runs (the grader reads it from there) and ran about one command per task; its numbers are about tool use, not reading.

## What round 7 changes in the round-5 reading

- **A fact the agent lacks is still where a guide is worth the most** (3/7 → 12/14), but "not on any web page" was doing more work than "not in the docs": Codex found this one on a forum.
- **A fact from the docs is dead weight, twice** (6/7 → 14/14 after 9/9 → 17/18).
- **"Two bugs" is not a kind.** The launchd story helped because its second fix was underivable; the DynamoDB story's second bug was in the fixture's own evidence, and 6 of 7 found it alone.
- **The trap kind now has a measurement:** 3 of 7 fell in without the story, 0 of 14 with it, 0 of 7 with it unmentioned in a folder.
- **A derivable cause gets found anyway, twice.**
- **"Method" splits:** a check the agent skips (s6) gets added; a method the agent already runs (s12) adds nothing.
- **Wording:** no difference in passes, twice. "Follow" copies the guide's request shapes; "a colleague's note" keeps what the evidence does not implicate.
- **The unmentioned note is read** (40 of 42) and is the fastest arm, twice.

## Incidents

One timeout: GPT-OSS on s7 without the story. No run leaked a secret; the `env` guard held. No external service was contacted with a credential; the only outbound calls were web searches and fetches of public pages (the Intervals forum, Anthropic and PostHog docs).

## Files

- `plan.md`: design and predictions, written before the runs.
- `table.md`: the pass grid, totals and every grader field per run.
- `prompts/`, `stories/`, `decoys/`, `fixtures/`, `graders/` (with `s7_probe.py`, the live Intervals probe).
- `runs/<story>-<agent>-<arm>-r1/`: `prompt.txt`, `agent.log`, `agent.err`, `diff.patch`, `grade.json`, `meta.json`, and the final `repo/`, shipped without its nested `.git` and without the scratch `workdir/`, as in rounds 4 to 6.
- `run.sh`, `lane.sh`, `all.sh`, `regrade.sh`, `make_table.py`: the harness. Paths are the author's machine.
