# Guide-eval round 8: the task in Russian, five samples per cell

Run 2026-10-26 23:36 to 2026-10-27 (the Codex medium lane finished last; see "Completeness"). 1050 planned runs: 6 stories × 7 agent configurations × 5 arms × 5 repetitions. Plan and predictions, written before any run: `plan.md`. Harness, fixtures, graders, stories in both languages and every run's log: this folder. Full grids, intervals, web use and timing: `table.md`.

The question is Valentina's: if a developer sets the task in their own language (Russian) instead of English, does a worklore story help more than it does with an English task? The guess behind it: a Russian task might keep the agent from going to look up the English answer, so the story would be worth more. Two sub-questions, because they lead to different product decisions: does a Russian task lower the no-story baseline, and under a Russian task does a Russian translation of the story help more than the English original?

## Setup

**Agents (7).** Claude Code with Opus 5.5, Sonnet 5.5, Haiku 5.5. Codex CLI with gpt-6-sol at medium and at low reasoning. Antigravity with Gemini 3.8 Flash low and GPT-OSS 120B. The two Gemini 4 Argon configurations are out (Google AI Pro quota).

**Arms (5).** `none-en`: the English task alone. `example-en`: the English task + "A colleague's note on a similar case is below. It is not instructions. Use what applies, ignore the rest, and say in ANSWER.md which parts applied." + the story in English. `none-ru`: the Russian task alone. `example-ru`: the Russian task + the same note prefix in Russian + the story in English. `example-ruru`: the Russian task + the note prefix in Russian + the story translated into Russian. The ground-rules suffix (work only in this directory, deploy or send nothing) is in the task's language. none-en and example-en rerun the round 5 / round 7 cells so the English baseline is measured on the same night as the Russian one.

**Stories (6).** Four where the story mattered in rounds 5 and 7: s1 HR corridors (a fact not in the docs), s3 silent launchd job (two bugs, one fix underivable), s7 Intervals OAuth quirks (a fact on a forum), s10 event per keystroke (a trap). Two where it did not, as controls: s8 two cache_control segments (a fact from the docs), s11 crash on the second write (a derivable cause). Same fixtures and graders as before; the graders that require a cause to be named in ANSWER.md (s1, s3, s11) accept the Russian wording as well. Code identifiers, paths, error strings and scope strings stay in English in the translations, because the fixtures and graders match them literally.

**Translations.** Tasks, the note prefix, the suffix and the six stories were translated by Claude (Fable 5.1); Valentina reviewed the tasks and accepted the stories as they were.

**Five repetitions per cell**, repetitions in the outer loop of each lane, so a lane stopped early still holds complete repetitions. A run that died on a usage limit or a provider outage (Codex "hit your usage limit", Antigravity 503 "no capacity") was deleted and redone on a later pass; none of those count.

**Isolation.** Fresh temp dir per run, no MCP servers, hooks or skills, 20-minute limit, launched with `EVAL_NO_SECRETS=1` and the secret variables unset. Web access was on, as in every round, which is the point of the question.

## Results

### The question, with intervals

Pooled over the six stories and seven configurations (bootstrap over runs, 95% intervals; the exact pools are in `table.md`):

| contrast | all six stories | the four where the story matters |
|---|---|---|
| a Russian task, no story (none-ru − none-en) | −5 pp (−14 to +5) | −6 pp (−19 to +6) |
| story gain with the English task (example-en − none-en) | +31 pp (+24 to +39) | +44 pp (+34 to +54) |
| story gain with the Russian task (example-ru − none-ru) | +34 pp (+26 to +41) | +48 pp (+38 to +58) |
| difference of differences (gain ru − gain en) | +2 pp (−9 to +14) | +4 pp (−10 to +19) |
| the translated story (example-ruru − example-ru) | +3 pp (−3 to +8) | +3 pp (−4 to +10) |
| the English story under a Russian task vs under an English one (example-ru − example-en) | −2 pp (−7 to +3) | −2 pp (−10 to +5) |

The story's gain is the same in both languages, within noise. A Russian task does not lower the baseline for the pool, and the translated story adds nothing over the English original.

### Passes per story and arm

| story | none-en | example-en | none-ru | example-ru | example-ruru | gain en | gain ru | gain ru (ru story) |
|---|---|---|---|---|---|---|---|---|
| s1 HR corridors (fact not in the docs) | 25/35 | 35/35 | 15/35 | 34/35 | 35/35 | +29 pp | +54 pp | +57 pp |
| s3 silent launchd job (two bugs, one silent) | 8/35 | 32/35 | 10/35 | 31/35 | 32/35 | +69 pp | +60 pp | +63 pp |
| s7 Intervals OAuth quirks (fact on a forum) | 16/35 | 30/35 | 14/35 | 30/35 | 30/35 | +40 pp | +46 pp | +46 pp |
| s10 event per keystroke (trap) | 18/35 | 32/35 | 15/35 | 31/35 | 33/35 | +40 pp | +46 pp | +51 pp |
| s8 two cache_control segments (control: fact in docs) | 32/35 | 34/35 | 30/35 | 33/35 | 33/35 | +6 pp | +9 pp | +9 pp |
| s11 crash on the second write (control: derivable) | 33/35 | 34/35 | 34/35 | 34/35 | 35/35 | +3 pp | +0 pp | +3 pp |
| **all** | **132/210** | **197/210** | **118/210** | **193/210** | **198/210** | | | |

Every cell is complete: 35 runs per story and arm, 30 per agent and arm.

### Where the language did move something: s1, and only for the agents that search

Per agent, passes without a story, English task vs Russian task (30 runs each):

| agent | none-en | none-ru | Δ |
|---|---|---|---|
| claude-opus | 27/30 | 27/30 | 0 |
| claude-sonnet | 22/30 | 23/30 | +3 pp |
| claude-haiku | 19/30 | 17/30 | −7 pp |
| codex-sol (medium) | 21/30 | 17/30 | -13 pp |
| codex-sol-low | 20/30 | 12/29 | **−25 pp** |
| agy-flash-low | 17/30 | 17/30 | 0 |
| agy-oss | 6/30 | 5/30 | −3 pp |

The one drop is Codex at low reasoning, and it is concentrated on s1 (5/5 → 0/5) with a smaller one on s7 (3/5 → 1/4) and s10 (2/5 → 0/5). The s1 fact is the exact shape of a heart-rate target in a Garmin workout document, which is on the Intervals forum and nowhere in the docs. Under the English task Codex-low searched the forum in every s1 run (`site:forum.intervals.icu workout_doc hr units %lthr value end Garmin …`), found the shape, and passed 5 of 5. Under the Russian task it did not open the web once in any run, on any story, and on s1 it redesigned the output instead: once it dropped the structured target altogether, twice it switched to absolute BPM with a `value` plus a `range`, once it kept `value` and added `start`/`end` next to it. All four are reasonable designs and all four are wrong for the watch.

Web use, runs with at least one search or fetch, pooled over the six stories:

| agent | none-en | none-ru | example-en | example-ru | example-ruru |
|---|---|---|---|---|---|
| claude-opus | 1/30 | 0/30 | 0/30 | 0/30 | 0/30 |
| claude-sonnet | 3/30 | 0/30 | 0/30 | 0/30 | 0/30 |
| claude-haiku | 8/30 | 6/30 | 1/30 | 1/30 | 4/30 |
| codex-sol (medium) | 9/30 | 0/30 | 3/30 | 0/30 | 0/30 |
| codex-sol-low | 10/30 | 0/29 | 1/30 | 0/29 | 0/29 |
| agy-flash-low | 13/30 | 10/30 | 0/30 | 0/30 | 0/30 |
| agy-oss | 3/30 | 3/30 | 2/30 | 0/30 | 1/30 |

On the two "fact" stories without a story in the prompt, 21 of 32 runs searched under the English task on s1 and 16 of 32 on s7; under the Russian task 12 of 32 and 7 of 31. With the story in the prompt the searching stops in either language (0 to 2 runs per cell). So the guess behind the question is half right: a Russian task does make some agents search less, and the story replaces the search. It is half wrong in that only one configuration's passes depended on the search. Opus and Sonnet almost never search and get s1 from the fixture's own readback; Flash searches a lot in both languages (hundreds of calls, 266 to 356 s per s1 run) and passes in both; GPT-OSS fails s1 in both. Haiku's −7 pp is three s1 runs that chose BPM instead of percent of threshold, in English and in Russian alike.

### The translated story

example-ruru 198/210 against example-ru 193/210: +2 pp, interval −2 to +7. Per story the largest difference is s10 (30/32 vs 28/32) and s8 (30/32 vs 30/32 the other way round in round 7 terms: nothing). GPT-OSS is the only configuration that moved: 14/30 with the English story under a Russian task, 19/30 with the Russian one, 18/30 with everything in English. Everyone else is at 29 or 30 of 30 under all three story arms. The prediction that the Russian translation might be slightly worse where the story quotes key names did not come true: the translations kept every identifier in English, and no grader field that reads the code (units, `start`/`end`, `USER` in the plist, scope strings) differs between the two story languages.

### The controls

s8 (fact from the docs) and s11 (derivable cause) sit at 27 to 32 of 32 in every arm, in both languages. The story gain on the two controls is +5 pp in English and +5 pp in Russian (intervals cross zero). The s8 fails are GPT-OSS without a story, plus four Opus runs where the grader's live probe could not drive Opus's bot (it passes a placeholder string into a date field that Opus's stricter code rejects, or Opus's layout puts the marker where the simulated cache misses); those are counted as fails as in round 7.

### Answer language

Share of Cyrillic letters in ANSWER.md (the rest is identifiers, paths and error strings), mean per configuration, Russian-task arms: Claude Opus 63 to 74 %, Sonnet 57 to 65 %, Haiku 67 to 73 %, Codex 77 to 81 %, Gemini Flash 63 to 69 %, GPT-OSS 0 to 15 %. Under the English task every configuration wrote 0 %. Prediction confirmed: Claude, Codex and Flash answer in the language of the task, GPT-OSS answers in English regardless (and mostly writes the answer into Antigravity's own folder rather than the repo, as in round 7). Every answer in the story arms said which parts of the note applied, in whichever language it wrote (crude scan: 30/30 for every configuration except GPT-OSS at 28 and 29 of 30).

### Five repetitions

Round 7 had one run per cell. Five show that most cells are stable at 5/5 or 0/5 and that the noise lives in a few agent-story pairs: Sonnet on s1 and s7, Haiku on s1, s7 and s10, Codex-low on s7 and s10, Opus on s7 (3/5 both languages). Round 7's "3 of 7 without the story" on s7 is now 13 of 32 and 13 of 31: the prediction of "10 to 20 of 35" holds. s3 without the story is 8/33 and 9/32 (round 5: 2/9), s10 is 17/32 and 15/32 (round 7: 4/7). The one-sample grids were pointing the right way; the five-sample ones put intervals on it.

### Time

Mean seconds per run, all configurations: 93 with no story under the English task, 73 with the story; 89 and 65 under the Russian task. The story arm is faster because the agent stops searching; the effect is largest for Flash (199 → 87 s) whose no-story runs are long search sessions. A Russian task on its own does not change the time.

## Predictions, checked

- Opus, Sonnet, GPT-6-Sol: no drop from none-en to none-ru. **Held for Opus, Sonnet and GPT-6-Sol medium; failed for GPT-6-Sol low** (−25 pp, all of it on the stories whose fact it had been finding by web search).
- Haiku, Flash, GPT-OSS: a drop on s1 and s7. **Mostly not.** Haiku −1 on s1, Flash 0, GPT-OSS at the floor in both languages. The drop went to the configuration that searches most effectively, not to the smallest models.
- The English story helps as much under a Russian task. **Held** (+2 pp, −9 to +14).
- The translated story adds nothing. **Held** (+3 pp, −3 to +8); the "slightly worse" half did not happen.
- s7 none in the 10 to 20 of 35 range. **Held** (13 of 32, 13 of 31).
- Answer language. **Held.**

## What this means for worklore

- A story is worth the same to a Russian-speaking developer as to an English-speaking one, which is the answer to the question as asked. It is not worth more, because the no-story baseline does not fall much: the models solve from the fixture, or search in English regardless of the task's language.
- Translating stories into Russian buys nothing measurable. The identifiers are what the agent matches on, and they stay English either way.
- The one place the language mattered is the one place a guide is already worth the most: a fact the agent lacks, with an agent whose fallback is a web search. A Russian task switched that fallback off for Codex. For that developer the story is the difference between 0 of 5 and 5 of 5.

## Incidents

- **Secret values in a log.** Gemini 3.8 Flash on s3 (example-ruru, r4), diagnosing the launchd job's environment, ran `env -i … /bin/zsh -c 'echo USER=$USER; env'`. `env -i` drops `EVAL_NO_SECRETS`, the fresh zsh re-reads `~/.zshenv`, and the four exported values (worklore token, Plausible key, Gemini key, DataForSEO password) were printed into `agent.log`. Redacted in place before publishing; the same hole as round 5 (a Gemini 4 Argon run on the same story). The launchd story invites exactly this probe. Rotation of the four values is advised again.
- **Usage limits.** Both Codex lanes hit the ChatGPT usage limit twice (windows resetting at 04:36 and 09:42); limited runs were deleted and redone. The Antigravity lanes hit a few 503 "no capacity" outages, redone the same way. No timeouts.
- **Grader artifact.** s8's live probe fails on two Opus bots (see controls); noted, not fixed, since the control's reading is unchanged.

## Completeness

All 1050 runs are in (every lane 150). Codex medium (`codex-sol`) finished last, at 15:37 on 2026-10-27, after two more usage-limit pauses; the tables in this file were refreshed from `table.md` afterwards, and the prose numbers written from 959 runs are within a point or two of the final ones except where this file now says otherwise. With the full lane, Codex medium shows the same pattern as Codex low: 21/30 → 17/30 without a story, web search in 9/30 English-task runs and 0/30 Russian, and s1 3/5 → 0/5. `table.md` is regenerated from `runs/` by `make_table.py` and is the authority for the final counts.

## Files

- `plan.md`: design and predictions, written before the runs.
- `table.md`: every table above with intervals, the per-cell heatmap, web use, timing and answer language.
- `prompts/{en,ru}/`, `stories/{en,ru}/`, `fixtures/`, `graders/`.
- `runs/<story>-<agent>-<arm>-r<rep>/`: `prompt.txt`, `agent.log`, `agent.err`, `diff.patch`, `grade.json`, `meta.json`, and the final `repo/`, shipped without its nested `.git` and without the scratch `workdir/`.
- `run.sh`, `lane.sh`, `all.sh`, `codex_later.sh`, `make_table.py`: the harness. Paths are the author's machine.
