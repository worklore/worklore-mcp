# Round 8 tables

## Passes per story and arm (five repetitions × nine agents = 45 runs per cell when complete)

| story | none-en | example-en | none-ru | example-ru | example-ruru | gain en | gain ru | gain ru (ru story) |
|---|---|---|---|---|---|---|---|---|
| s1 HR corridors (fact not in the docs) | 32/45 | 45/45 | 19/45 | 44/45 | 45/45 | +29 pp | +56 pp | +58 pp |
| s3 silent launchd job (two bugs, one silent) | 10/45 | 42/45 | 11/45 | 41/45 | 42/45 | +71 pp | +67 pp | +69 pp |
| s7 Intervals OAuth quirks (fact on a forum) | 22/45 | 40/45 | 16/45 | 40/45 | 40/45 | +40 pp | +53 pp | +53 pp |
| s10 event per keystroke (trap) | 20/45 | 42/45 | 17/45 | 41/45 | 43/45 | +49 pp | +53 pp | +58 pp |
| s8 two cache_control segments (control: fact in docs) | 42/45 | 44/45 | 40/45 | 43/45 | 43/45 | +4 pp | +7 pp | +7 pp |
| s11 crash on the second write (control: derivable) | 43/45 | 44/45 | 44/45 | 44/45 | 45/45 | +2 pp | +0 pp | +2 pp |
| **all** | **169/270** | **257/270** | **147/270** | **253/270** | **258/270** | | | |

## Passes per agent and arm (six stories × five repetitions = 30 runs per cell when complete)

| agent | none-en | example-en | none-ru | example-ru | example-ruru |
|---|---|---|---|---|---|
| claude-opus | 27/30 | 29/30 | 27/30 | 29/30 | 29/30 |
| claude-sonnet | 22/30 | 30/30 | 23/30 | 30/30 | 30/30 |
| claude-haiku | 19/30 | 30/30 | 17/30 | 30/30 | 30/30 |
| codex-sol | 21/30 | 30/30 | 17/30 | 30/30 | 30/30 |
| codex-sol-low | 20/30 | 30/30 | 12/30 | 30/30 | 30/30 |
| agy-flash-low | 17/30 | 30/30 | 17/30 | 30/30 | 30/30 |
| agy-oss | 6/30 | 18/30 | 5/30 | 14/30 | 19/30 |
| kimi-k28 | 19/30 | 30/30 | 17/30 | 30/30 | 30/30 |
| kimi-k31 | 18/30 | 30/30 | 12/30 | 30/30 | 30/30 |

## Per cell: passes out of the repetitions run (the heatmap)

### s1: HR corridors (fact not in the docs)

| agent | none-en | example-en | none-ru | example-ru | example-ruru | mean s per arm |
|---|---|---|---|---|---|---|
| claude-opus | 4/5 | 5/5 | 5/5 | 5/5 | 5/5 | 51/34/49/38/41 |
| claude-sonnet | 4/5 | 5/5 | 3/5 | 5/5 | 5/5 | 23/20/29/22/22 |
| claude-haiku | 3/5 | 5/5 | 2/5 | 5/5 | 5/5 | 41/22/44/26/27 |
| codex-sol | 3/5 | 5/5 | 0/5 | 5/5 | 5/5 | 78/34/115/40/39 |
| codex-sol-low | 5/5 | 5/5 | 0/5 | 5/5 | 5/5 | 47/28/56/30/29 |
| agy-flash-low | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 266/44/356/49/50 |
| agy-oss | 1/5 | 5/5 | 0/5 | 4/5 | 5/5 | 77/33/88/43/40 |
| kimi-k28 | 4/5 | 5/5 | 2/5 | 5/5 | 5/5 | 358/83/341/84/84 |
| kimi-k31 | 3/5 | 5/5 | 2/5 | 5/5 | 5/5 | 153/72/122/117/96 |

### s3: silent launchd job (two bugs, one silent)

| agent | none-en | example-en | none-ru | example-ru | example-ruru | mean s per arm |
|---|---|---|---|---|---|---|
| claude-opus | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 61/60/85/87/86 |
| claude-sonnet | 1/5 | 5/5 | 1/5 | 5/5 | 5/5 | 26/25/30/28/28 |
| claude-haiku | 1/5 | 5/5 | 0/5 | 5/5 | 5/5 | 67/79/61/66/117 |
| codex-sol | 1/5 | 5/5 | 3/5 | 5/5 | 5/5 | 103/103/118/104/105 |
| codex-sol-low | 0/5 | 5/5 | 1/5 | 5/5 | 5/5 | 44/44/45/38/65 |
| agy-flash-low | 0/5 | 5/5 | 0/5 | 5/5 | 5/5 | 191/55/82/55/97 |
| agy-oss | 0/5 | 2/5 | 0/5 | 1/5 | 2/5 | 79/79/94/51/54 |
| kimi-k28 | 2/5 | 5/5 | 1/5 | 5/5 | 5/5 | 388/219/273/317/252 |
| kimi-k31 | 0/5 | 5/5 | 0/5 | 5/5 | 5/5 | 158/144/157/175/174 |

### s7: Intervals OAuth quirks (fact on a forum)

| agent | none-en | example-en | none-ru | example-ru | example-ruru | mean s per arm |
|---|---|---|---|---|---|---|
| claude-opus | 3/5 | 5/5 | 3/5 | 5/5 | 5/5 | 100/89/116/117/102 |
| claude-sonnet | 2/5 | 5/5 | 4/5 | 5/5 | 5/5 | 37/30/35/45/50 |
| claude-haiku | 1/5 | 5/5 | 2/5 | 5/5 | 5/5 | 174/125/173/109/119 |
| codex-sol | 5/5 | 5/5 | 3/5 | 5/5 | 5/5 | 122/132/134/117/126 |
| codex-sol-low | 3/5 | 5/5 | 1/5 | 5/5 | 5/5 | 66/64/55/65/77 |
| agy-flash-low | 2/5 | 5/5 | 1/5 | 5/5 | 5/5 | 366/175/276/155/137 |
| agy-oss | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 253/240/272/155/145 |
| kimi-k28 | 1/5 | 5/5 | 2/5 | 5/5 | 5/5 | 830/504/792/566/577 |
| kimi-k31 | 5/5 | 5/5 | 0/5 | 5/5 | 5/5 | 316/280/259/347/267 |

### s10: event per keystroke (trap)

| agent | none-en | example-en | none-ru | example-ru | example-ruru | mean s per arm |
|---|---|---|---|---|---|---|
| claude-opus | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 57/59/62/65/61 |
| claude-sonnet | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 27/22/25/25/31 |
| claude-haiku | 4/5 | 5/5 | 3/5 | 5/5 | 5/5 | 51/103/55/57/58 |
| codex-sol | 2/5 | 5/5 | 1/5 | 5/5 | 5/5 | 85/88/95/93/111 |
| codex-sol-low | 2/5 | 5/5 | 0/5 | 5/5 | 5/5 | 51/59/56/56/61 |
| agy-flash-low | 0/5 | 5/5 | 1/5 | 5/5 | 5/5 | 202/112/96/99/98 |
| agy-oss | 0/5 | 2/5 | 0/5 | 1/5 | 3/5 | 360/335/183/129/177 |
| kimi-k28 | 2/5 | 5/5 | 2/5 | 5/5 | 5/5 | 275/257/201/199/189 |
| kimi-k31 | 0/5 | 5/5 | 0/5 | 5/5 | 5/5 | 178/168/170/163/149 |

### s8: two cache_control segments (control: fact in docs)

| agent | none-en | example-en | none-ru | example-ru | example-ruru | mean s per arm |
|---|---|---|---|---|---|---|
| claude-opus | 5/5 | 4/5 | 4/5 | 4/5 | 4/5 | 133/149/122/147/137 |
| claude-sonnet | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 24/37/45/25/22 |
| claude-haiku | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 51/65/44/65/77 |
| codex-sol | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 127/107/115/99/113 |
| codex-sol-low | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 59/43/51/34/34 |
| agy-flash-low | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 102/66/131/65/61 |
| agy-oss | 2/5 | 5/5 | 1/5 | 4/5 | 4/5 | 36/48/34/52/43 |
| kimi-k28 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 387/204/210/221/191 |
| kimi-k31 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 105/111/133/109/124 |

### s11: crash on the second write (control: derivable)

| agent | none-en | example-en | none-ru | example-ru | example-ruru | mean s per arm |
|---|---|---|---|---|---|---|
| claude-opus | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 43/56/50/58/50 |
| claude-sonnet | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 19/25/26/23/26 |
| claude-haiku | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 32/39/39/46/51 |
| codex-sol | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 49/49/45/66/57 |
| codex-sol-low | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 31/35/31/37/34 |
| agy-flash-low | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 69/70/90/75/74 |
| agy-oss | 3/5 | 4/5 | 4/5 | 4/5 | 5/5 | 43/29/33/46/37 |
| kimi-k28 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 100/113/107/123/111 |
| kimi-k31 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 124/119/129/144/178 |

## Answer language: share of Cyrillic letters in ANSWER.md, mean per agent and arm

| agent | none-en | example-en | none-ru | example-ru | example-ruru |
|---|---|---|---|---|---|
| claude-opus | 0% | 0% | 63% | 65% | 74% |
| claude-sonnet | 0% | 0% | 65% | 57% | 64% |
| claude-haiku | 0% | 0% | 67% | 71% | 73% |
| codex-sol | 0% | 0% | 79% | 80% | 80% |
| codex-sol-low | 0% | 0% | 74% | 79% | 79% |
| agy-flash-low | 0% | 0% | 63% | 69% | 69% |
| agy-oss | 0% | 0% | 15% | 0% | · |
| kimi-k28 | 0% | 0% | 69% | 72% | 74% |
| kimi-k31 | 0% | 0% | 75% | 76% | 76% |

## The question, with intervals (bootstrap over runs, 95%)

| contrast | stories | estimate | 95% CI |
|---|---|---|---|
| task in Russian, no story: none-ru − none-en | all six | -8 pp | -16 pp to +0 pp |
| story gain in English: example-en − none-en | all six | +33 pp | +26 pp to +39 pp |
| story gain in Russian: example-ru − none-ru | all six | +39 pp | +33 pp to +46 pp |
| difference of differences: gain ru − gain en | all six | +7 pp | -3 pp to +16 pp |
| translated story: example-ruru − example-ru | all six | +2 pp | -2 pp to +6 pp |
| Russian task with the English story vs English task with it: example-ru − example-en | all six | -1 pp | -6 pp to +2 pp |
| task in Russian, no story: none-ru − none-en | the four where the story mattered | -12 pp | -22 pp to -2 pp |
| story gain in English: example-en − none-en | the four where the story mattered | +47 pp | +39 pp to +56 pp |
| story gain in Russian: example-ru − none-ru | the four where the story mattered | +57 pp | +49 pp to +66 pp |
| difference of differences: gain ru − gain en | the four where the story mattered | +10 pp | -1 pp to +22 pp |
| translated story: example-ruru − example-ru | the four where the story mattered | +2 pp | -3 pp to +7 pp |
| Russian task with the English story vs English task with it: example-ru − example-en | the four where the story mattered | -2 pp | -7 pp to +4 pp |
| task in Russian, no story: none-ru − none-en | the two controls | -1 pp | -8 pp to +6 pp |
| story gain in English: example-en − none-en | the two controls | +3 pp | -2 pp to +9 pp |
| story gain in Russian: example-ru − none-ru | the two controls | +3 pp | -2 pp to +10 pp |
| difference of differences: gain ru − gain en | the two controls | +0 pp | -8 pp to +9 pp |
| translated story: example-ruru − example-ru | the two controls | +1 pp | -3 pp to +6 pp |
| Russian task with the English story vs English task with it: example-ru − example-en | the two controls | -1 pp | -6 pp to +3 pp |

## Task language per agent: passes without a story, English vs Russian task (30 runs each when complete)

| agent | none-en | none-ru | Δ | example-en | example-ru | example-ruru |
|---|---|---|---|---|---|---|
| claude-opus | 27/30 | 27/30 | +0 pp | 29/30 | 29/30 | 29/30 |
| claude-sonnet | 22/30 | 23/30 | +3 pp | 30/30 | 30/30 | 30/30 |
| claude-haiku | 19/30 | 17/30 | -7 pp | 30/30 | 30/30 | 30/30 |
| codex-sol | 21/30 | 17/30 | -13 pp | 30/30 | 30/30 | 30/30 |
| codex-sol-low | 20/30 | 12/30 | -27 pp | 30/30 | 30/30 | 30/30 |
| agy-flash-low | 17/30 | 17/30 | +0 pp | 30/30 | 30/30 | 30/30 |
| agy-oss | 6/30 | 5/30 | -3 pp | 18/30 | 14/30 | 19/30 |
| kimi-k28 | 19/30 | 17/30 | -7 pp | 30/30 | 30/30 | 30/30 |
| kimi-k31 | 18/30 | 12/30 | -20 pp | 30/30 | 30/30 | 30/30 |

## Web use: runs with at least one web search or fetch (and the number of calls), per agent and arm

Counted from the harness logs: Claude Code `WebSearch`/`WebFetch` tool calls, Codex `web_search` events, Antigravity `search_web`/`read_url_content` calls (each step once; before 2026-11-09 a step was counted once per logged state, which doubled the number of calls).

| agent | none-en | example-en | none-ru | example-ru | example-ruru |
|---|---|---|---|---|---|
| claude-opus | 1/30 (1) | 0/30 (0) | 0/30 (0) | 0/30 (0) | 0/30 (0) |
| claude-sonnet | 3/30 (4) | 0/30 (0) | 0/30 (0) | 0/30 (0) | 0/30 (0) |
| claude-haiku | 8/30 (10) | 1/30 (1) | 6/30 (8) | 1/30 (1) | 4/30 (4) |
| codex-sol | 9/30 (27) | 3/30 (3) | 0/30 (0) | 0/30 (0) | 0/30 (0) |
| codex-sol-low | 10/30 (23) | 1/30 (1) | 0/30 (0) | 0/30 (0) | 0/30 (0) |
| agy-flash-low | 13/30 (238) | 0/30 (0) | 10/30 (213) | 0/30 (0) | 0/30 (0) |
| agy-oss | 3/30 (7) | 2/30 (4) | 3/30 (3) | 0/30 (0) | 1/30 (1) |
| kimi-k28 | 13/30 (69) | 0/30 (0) | 6/30 (32) | 0/30 (0) | 0/30 (0) |
| kimi-k31 | 6/30 (25) | 0/30 (0) | 0/30 (0) | 0/30 (0) | 0/30 (0) |

### Web use per story, all agents: runs with a web call / runs

| story | none-en | example-en | none-ru | example-ru | example-ruru |
|---|---|---|---|---|---|
| s1 | 31/45 | 0/45 | 14/45 | 1/45 | 2/45 |
| s3 | 1/45 | 0/45 | 0/45 | 0/45 | 0/45 |
| s7 | 27/45 | 2/45 | 11/45 | 0/45 | 1/45 |
| s10 | 0/45 | 0/45 | 0/45 | 0/45 | 0/45 |
| s8 | 7/45 | 5/45 | 0/45 | 0/45 | 2/45 |
| s11 | 0/45 | 0/45 | 0/45 | 0/45 | 0/45 |

## Wall time: mean seconds per run, per arm

| agent | none-en | example-en | none-ru | example-ru | example-ruru |
|---|---|---|---|---|---|
| claude-opus | 74 | 75 | 80 | 85 | 80 |
| claude-sonnet | 26 | 26 | 32 | 28 | 30 |
| claude-haiku | 69 | 72 | 69 | 61 | 75 |
| codex-sol | 94 | 86 | 103 | 86 | 92 |
| codex-sol-low | 50 | 45 | 49 | 43 | 50 |
| agy-flash-low | 199 | 87 | 172 | 83 | 86 |
| agy-oss | 141 | 127 | 117 | 79 | 83 |
| kimi-k28 | 390 | 230 | 321 | 252 | 234 |
| kimi-k31 | 172 | 149 | 162 | 176 | 165 |
| all | 135 | 100 | 123 | 99 | 99 |

## Runs that are not results

- s1-kimi-k28-none-en-r1: exit 124 (timeout), 1200 s
- s7-kimi-k28-none-en-r5: exit 124 (timeout), 1200 s

