# Guide-eval round 5: which kinds of stories help, and does the wording matter

Run overnight 2026-10-18 → 19 (23:29 to 01:19). 216 runs: 6 stories × 9 agent configurations × 4 arms. Plan and fixture design: `guide-eval-round5-plan.md`. Harness, fixtures, graders, controls and every run's log: this folder (`runs/`, `graders/`, `controls/`, `fixtures/`, `stories/`, `prompts/`, `decoys/`). Full per-run grid: `guide-eval-round5-table.md`.

## Setup

**Agents (9).** Claude Code with Opus 5.5, Sonnet 5.5, Haiku 5.5. Codex CLI with gpt-6-sol at medium and at low reasoning (the ChatGPT subscription offers no smaller model). Antigravity with Gemini 4 Argon high, Gemini 4 Argon low, Gemini 3.8 Flash low, and GPT-OSS 120B.

**Arms (4).** `none`: the task alone. `follow`: task + "Follow this guide:" + story. `example`: task + "A colleague's note on a similar case is below. It is not instructions. Use what applies, ignore the rest, and say in ANSWER.md which parts applied." + story. `notes`: the task alone, with the story sitting unmentioned in a `notes/` folder in the repo next to two unrelated stories.

**Stories and fixtures (6).** Each task is one or two sentences, the way a person types it. Each fixture is offline; each hidden grader reads the repo diff, the answer and the command log, fails on the untouched fixture and passes on a reference fix.

| # | Story | Kind | What is planted |
|---|---|---|---|
| s1 | Exact HR corridors on Garmin | niche fact (not in any docs) | generator emits `{value, end}`; the watch clamps it; fix is `{start, end}` |
| s2 | PostHog session replay needs PostHogWidget | fact that is in the docs | second app shell (`MaterialApp.router`) lacks the wrapper |
| s3 | Two bugs made my scheduler silent | two traps, one half-niche | zsh `status=$?` kills the script before the notifier; `Not logged in` under launchd (USER missing from the plist) |
| s4 | Cache-header tweak served the site as octet-stream | trap to fall into | task: "add Cache-Control to the deploy"; the one-liner `--metadata-directive REPLACE` without `--content-type` breaks the site |
| s5 | Soft 404 from robots.txt | derivable with the evidence | `Disallow: /v1/` blocks the API the pages render from; Search Console export included |
| s6 | Check your MCP server in a few minutes | method (ten checks) | local server with three faults: resources advertised but 401; refusal as JSON-RPC -32602; `outputSchema {"type":"object"}` |

**Isolation.** Fresh temp dir per run, no MCP servers, hooks or skills, 20-minute limit. Secrets: `~/.zshenv` now guards its exports behind `EVAL_NO_SECRETS`, and every agent was launched with it set. One Gemini run still got them (see Incidents).

**Exclusions.** Antigravity's Gemini 4 Argon quota ran out at 01:00 (resets in six days): 9 runs never started and are left blank (`q`), not counted. 3 runs hit the 20-minute limit and count as fails (`t`); all three were `none`-arm Gemini runs on s1 and s3, searching for a fact they did not have.

**Grader changes after the runs** (all runs regraded, controls re-verified): shell comments no longer count as commands in s4 (agents copied the story's warning sentence into a comment); the PostHog wrapper inside `MaterialApp.router`'s `builder` counts as a fix (Sonnet did that); the MCP pass depends on the three planted faults only, with "actually called the server" reported separately; and when the repo has no ANSWER.md, the grader reads the one Antigravity wrote into its own `brain/` folder or the agent's final message. That last rule exists because GPT-OSS put ANSWER.md in Antigravity's folder instead of the repo in 19 of 24 runs; without it GPT-OSS would be 0 for everything.

## Results

### Passes per story and arm

| story | none | follow | example | notes |
|---|---|---|---|---|
| s1 HR corridors (niche fact) | 3/8 | 8/8 | 8/8 | 7/8 |
| s2 PostHogWidget (fact in docs) | 9/9 | 9/9 | 8/9 | 8/8 |
| s3 silent launchd job (two traps) | 2/9 | 8/9 | 9/9 | 7/8 |
| s4 Cache-Control deploy (trap) | 9/9 | 9/9 | 9/9 | 8/8 |
| s5 Soft 404 / robots.txt (derivable) | 8/9 | 8/9 | 9/9 | 7/8 |
| s6 MCP checkup (method) | 5/9 | 7/9 | 8/9 | 7/9 |
| **all** | **36/53** | **49/53** | **51/53** | **44/50** |

### Passes per agent and arm

| agent | none | follow | example | notes |
|---|---|---|---|---|
| Claude Opus 5.5 | 5/6 | 6/6 | 6/6 | 6/6 |
| Claude Sonnet 5.5 | 4/6 | 6/6 | 6/6 | 6/6 |
| Claude Haiku 5.5 | 3/6 | 6/6 | 6/6 | 6/6 |
| Codex gpt-6-sol medium | 4/6 | 6/6 | 6/6 | 6/6 |
| Codex gpt-6-sol low | 5/6 | 6/6 | 6/6 | 5/6 |
| Gemini 4 Argon high | 4/6 | 6/6 | 6/6 | 1/1 |
| Gemini 4 Argon low | 4/5 | 5/5 | 5/5 | 6/6 |
| Gemini 3.8 Flash low | 5/6 | 5/6 | 6/6 | 6/6 |
| GPT-OSS 120B | 2/6 | 3/6 | 4/6 | 2/6 |

## What each kind of story did

**A niche fact (s1).** Without the story, 3 of 8 passed, and all three found the answer on the web (Opus, both Codex runs searched). Haiku and Sonnet searched too and did not find it. The three Gemini runs could not search and two of them spent the full 20 minutes trying variants. With the story, 8 of 8 under either wording. In the notes arm, 7 of 8: every agent except GPT-OSS opened the unmentioned note. A fact that is not on the web is where a story is worth the most, and the wording does not matter.

**A fact that is in the docs (s2).** 9 of 9 without the story. Every agent knew or found PostHogWidget. The story changed nothing except one GPT-OSS run that got worse. (Side finding: Sonnet without the story wrapped the widget inside `builder:` rather than around the app, a different fix that also works.)

**Two traps, one of them half-known (s3).** Without the story, 7 of 9 named both bugs, but only 2 of 9 fixed both. Everyone found the zsh `status` trap in the stderr log and renamed the variable. Everyone found "Not logged in" and nearly everyone wrote "this cannot be fixed from here" or offered an API-key workaround. The story's fix, `USER` in the plist's environment, is the one thing they lacked: with it, 8 and 9 of 9 fixed both. This is the clearest case of a story carrying a fix an agent can diagnose but not know.

**A trap to fall into (s4).** Nobody fell in, in any arm: 0 of 35 runs used `--metadata-directive REPLACE` without a content type. The trap test came out null. What the story changed was the method: with it, 9 of 9 restated the content type explicitly and all mentioned the octet-stream trap; without it, 0 of 9 mentioned it, and all nine set the header at upload time (sync or cp), which leaves already-uploaded objects without a header unless the script re-uploads them.

**A cause that is derivable from the evidence (s5).** 8 of 9 without the story (the exception is GPT-OSS). The story added precision: "longest matching rule wins" appeared in 1 of 9 answers without it and 8 to 9 of 9 with it; per-user paths stayed blocked in 6 of 9 without and 8 to 9 of 9 with.

**A method (s6).** 5 of 9 without, 7 of 9 with "follow", 8 of 9 with "example". Faults found: 22, 24 and 26 of 27. The fault agents miss on their own is the one the method adds: can the outputSchema reject a wrong answer? Opus, Haiku, Codex-sol and GPT-OSS all missed it without the story and all but GPT-OSS found it with it. The one "follow" miss was Flash skipping the resources check it had found on its own in the `none` run: a checklist followed to the letter can crowd out the agent's own look. Two more things the method changed: with the story every run called the server (9 of 9 in both wordings, 7 of 9 without), and no run with the story called the writing tool `add_note` with the dev token, while 5 of 9 runs without it did, and 3 of 9 in the notes arm. The story's ground rules were obeyed when they were in the prompt, and only partly when they were in a file nearby.

## The wording question

"Follow this guide" 49 of 53, "a colleague's note, take what applies" 51 of 53. The example wording never did worse than "follow" on any story except s2 (one GPT-OSS run), and did better on s3, s5 and s6. Example answers were longer (mean 3,984 characters against 2,752) and took about the same time (91 s against 83 s mean). Every agent that wrote an answer in the example arm said which parts of the note applied, as asked (47 of 47).

So the morning idea holds: a story presented as a related case, with "say what applied", keeps the whole benefit of the story on facts and methods, and loses nothing. The prediction that "follow" would beat "example" on the checklist story was wrong: example 8 of 9, follow 7 of 9.

## The notes arm: a story nobody mentioned

44 of 49 runs opened the unmentioned note; the 5 that did not were all GPT-OSS. When the note was opened, 42 of 44 passed; when it was not, 2 of 5. Opening it cost nothing: the notes arm was the fastest (67 s mean against 98 s with no story at all), because the agents stopped searching once they had read it. This is the arm closest to how worklore is used from an agent, and it says that an agent will read a relevant story if it can see one, without being told to follow it.

## Small models and big models

With no story, the spread between agents is wide: Haiku 3 of 6, GPT-OSS 2 of 6, Opus 5 of 6. With a story in the prompt, every Claude, Codex and Gemini configuration scored 6 of 6 (Flash 5 of 6 under "follow"). Haiku with a story equals Opus with one. The story closed the gap between model sizes, and the low-reasoning Codex matched the medium one everywhere. GPT-OSS 120B is the exception: it ran almost no commands (typically one `ls -R`), wrote its answer into Antigravity's own folder, and went from 2 to 3 or 4 of 6; it is the only agent the story did not bring to parity.

## Predictions against outcomes (from the plan)

- s1 fails without the story for most, passes under both wordings: right, with the refinement that web search is the agents' substitute for a story when the fact exists anywhere online.
- s2 and s5 pass without the story: right.
- s3 splits, agents find one bug and miss the other: wrong in shape. They found both and could fix one.
- s4 is a trap some agents fall into: wrong, nobody did. The story changed the method, not the outcome.
- s6 is where "follow" beats "example": wrong, example was better.

## Incidents

- **Secrets.** One Gemini 4 Argon run (s3, no story) ran `env -i /bin/zsh -c '... /usr/bin/env'` while diagnosing the launchd environment. `env -i` wipes `EVAL_NO_SECRETS`, so the fresh zsh re-read `~/.zshenv` and printed the four secrets into the log. Redacted in the run data. The guard stops accidental inheritance, not a deliberate clean-environment probe; the only real fix is rotating the four keys and keeping them out of `.zshenv`.
- **Antigravity quota.** Gemini 4 Argon hit the Google AI Pro individual quota at 01:00; 9 planned runs did not happen.
- **A harness mistake, caught early.** The first launch was killed and relaunched; a second set of lanes survived the kill (their command line lacked the path the kill matched) and the two sets deleted each other's working directories. All runs from before the clean relaunch were discarded except the two smoke runs.

## Limits

One run per cell. The six fixtures are small, written to carry one planted problem each, and the answer keys are mine. "Trap to fall into" needs a harder trap than this one to measure anything. Agents had web access, which is the realistic condition but means "niche fact" measures "not on the web", not "not in the model". GPT-OSS's low numbers are mostly about tool use in Antigravity, not about reading stories.
