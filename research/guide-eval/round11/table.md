# Round 11 tables

## Passes per agent and arm (five stories × five repetitions = 25 runs per cell when complete)

| agent | none | story | ticket |
|---|---|---|---|
| claude-haiku | 11/25 | 25/25 | 25/25 |
| codex-sol-low | 11/25 | 25/25 | 25/25 |
| codex-oss | 7/25 | 14/25 | 13/25 |
| vibe-devstral | 6/25 | 22/25 | 21/25 |
| kimi-k31 | · | · | · |

## The new stories only (n4, n6, n10: 15 runs per cell when complete), with the references

| agent | none | story | ticket |
|---|---|---|---|
| claude-haiku | 1/15 | 15/15 | 15/15 |
| codex-sol-low | 1/15 | 15/15 | 15/15 |
| codex-oss | 0/15 | 6/15 | 6/15 |
| vibe-devstral | 0/15 | 12/15 | 11/15 |
| kimi-k31 | · | · | · |
| claude-opus | 7/15 | · | · |
| agy-oss | 0/15 | 7/15 | · |

## Works, but on the old package (n6 WORKS_ON_OLD_SDK, n10 WORKS_ON_PRISMA7), runs per arm

| agent | story | none | story arm | ticket |
|---|---|---|---|---|
| claude-haiku | n6 | 4/5 | 0/5 | 0/5 |
| claude-haiku | n10 | 5/5 | 0/5 | 0/5 |
| codex-sol-low | n6 | 5/5 | 0/5 | 0/5 |
| codex-sol-low | n10 | 4/5 | 0/5 | 0/5 |
| codex-oss | n6 | 2/5 | 0/5 | 0/5 |
| codex-oss | n10 | 0/5 | 0/5 | 0/5 |
| vibe-devstral | n6 | 0/5 | 0/5 | 0/5 |
| vibe-devstral | n10 | 1/5 | 0/5 | 0/5 |
| claude-opus | n6 | 2/5 | · | · |
| claude-opus | n10 | 5/5 | · | · |
| agy-oss | n6 | 1/5 | 0/5 | · |
| agy-oss | n10 | 0/5 | 0/5 | · |

## Passes per story and arm, all round 11 agents except kimi-k31

| story | none | story | ticket |
|---|---|---|---|
| n4 Codex -o under a sandbox: empty answer, exit 0 (trap) | 1/20 | 19/20 | 18/20 |
| n6 Hedera SDK moved to @hiero-ledger/sdk (fact not on npm) | 0/20 | 13/20 | 12/20 |
| n10 Prisma 8 has no @prisma/client (fact not on npm) | 1/20 | 16/20 | 17/20 |
| s8 two cache_control segments (control: fact in docs) | 14/20 | 18/20 | 17/20 |
| s11 crash on the second write (control: derivable) | 19/20 | 20/20 | 20/20 |

## Per cell (the heatmap)

### n4: Codex -o under a sandbox: empty answer, exit 0 (trap)

| agent | none | story | ticket |
|---|---|---|---|
| claude-haiku | 1/5 | 5/5 | 5/5 |
| codex-sol-low | 0/5 | 5/5 | 5/5 |
| codex-oss | 0/5 | 4/5 | 3/5 |
| vibe-devstral | 0/5 | 5/5 | 5/5 |
| kimi-k31 | · | · | · |
| claude-opus | 4/5 | · | · |
| agy-oss | 0/5 | 5/5 | · |

### n6: Hedera SDK moved to @hiero-ledger/sdk (fact not on npm)

| agent | none | story | ticket |
|---|---|---|---|
| claude-haiku | 0/5 | 5/5 | 5/5 |
| codex-sol-low | 0/5 | 5/5 | 5/5 |
| codex-oss | 0/5 | 1/5 | 1/5 |
| vibe-devstral | 0/5 | 2/5 | 1/5 |
| kimi-k31 | · | · | · |
| claude-opus | 3/5 | · | · |
| agy-oss | 0/5 | 2/5 | · |

### n10: Prisma 8 has no @prisma/client (fact not on npm)

| agent | none | story | ticket |
|---|---|---|---|
| claude-haiku | 0/5 | 5/5 | 5/5 |
| codex-sol-low | 1/5 | 5/5 | 5/5 |
| codex-oss | 0/5 | 1/5 | 2/5 |
| vibe-devstral | 0/5 | 5/5 | 5/5 |
| kimi-k31 | · | · | · |
| claude-opus | 0/5 | · | · |
| agy-oss | 0/5 | 0/5 | · |

### s8: two cache_control segments (control: fact in docs)

| agent | none | story | ticket |
|---|---|---|---|
| claude-haiku | 5/5 | 5/5 | 5/5 |
| codex-sol-low | 5/5 | 5/5 | 5/5 |
| codex-oss | 3/5 | 3/5 | 2/5 |
| vibe-devstral | 1/5 | 5/5 | 5/5 |
| kimi-k31 | · | · | · |

### s11: crash on the second write (control: derivable)

| agent | none | story | ticket |
|---|---|---|---|
| claude-haiku | 5/5 | 5/5 | 5/5 |
| codex-sol-low | 5/5 | 5/5 | 5/5 |
| codex-oss | 4/5 | 5/5 | 5/5 |
| vibe-devstral | 5/5 | 5/5 | 5/5 |
| kimi-k31 | · | · | · |

## The three questions (plan.md), with 95% bootstrap intervals

| question | comparison | value | 95% CI |
|---|---|---|---|
| A: open + story vs frontier alone | codex-oss story (6/15) − Opus none, n4/n6/n10 (7/15) | -7 pp | -40 pp to +27 pp |
| A: open + story vs frontier alone | vibe-devstral story (12/15) − Opus none, n4/n6/n10 (7/15) | +33 pp | +0 pp to +67 pp |
| B: GPT-OSS harness | codex-oss none (0/15) − agy-oss none, n4/n6/n10 (0/15) | +0 pp | +0 pp to +0 pp |
| B: GPT-OSS harness | codex-oss story (6/15) − agy-oss story, n4/n6/n10 (7/15) | -7 pp | -40 pp to +27 pp |
| C: story vs ticket, n4/n6/n10 | claude-haiku: story 15/15, ticket 15/15 | +0 pp | +0 pp to +0 pp |
| C: story vs ticket, n4/n6/n10 | codex-sol-low: story 15/15, ticket 15/15 | +0 pp | +0 pp to +0 pp |
| C: story vs ticket, n4/n6/n10 | codex-oss: story 6/15, ticket 6/15 | +0 pp | -33 pp to +33 pp |
| C: story vs ticket, n4/n6/n10 | vibe-devstral: story 12/15, ticket 11/15 | +7 pp | -27 pp to +33 pp |
| C: story vs ticket, n4/n6/n10 | all four round 11 agents: story 48/60, ticket 47/60 | +2 pp | -13 pp to +17 pp |

## Cost of the OpenRouter lanes

Vibe: `cost_usd` from its export. Codex: token usage from `turn.completed` events × OpenRouter's price.

| agent | arm | runs | tokens in (cached) / out | cost $ | $ per run |
|---|---|---|---|---|---|
| codex-oss | none | 25 | 16,192,390 (13,939,773) / 320,475 | 2.62 | 0.105 |
| codex-oss | story | 25 | 15,293,138 (12,483,123) / 285,559 | 2.47 | 0.099 |
| codex-oss | ticket | 25 | 29,500,110 (25,973,688) / 476,449 | 4.71 | 0.188 |
| vibe-devstral | none | 25 | 25,501,091 (24,673,536) / 127,623 | 10.46 | 0.418 |
| vibe-devstral | story | 25 | 17,092,091 (16,408,064) / 118,755 | 7.07 | 0.283 |
| vibe-devstral | ticket | 25 | 21,945,133 (21,190,400) / 146,446 | 9.07 | 0.363 |

## Web use: runs with at least one web search or fetch (calls), per agent and arm

| agent | none | story | ticket |
|---|---|---|---|
| claude-haiku | 0/25 (0) | 0/25 (0) | 0/25 (0) |
| codex-sol-low | 1/25 (3) | 3/25 (4) | 5/25 (8) |
| codex-oss | 0/25 (0) | 0/25 (0) | 0/25 (0) |
| vibe-devstral | 0/25 (0) | 0/25 (0) | 0/25 (0) |
| kimi-k31 | · | · | · |
| claude-opus | 0/15 (0) | · | · |
| agy-oss | 4/15 (16) | 2/15 (4) | · |

## Wall time: mean seconds per run

| agent | none | story | ticket |
|---|---|---|---|
| claude-haiku | 80 | 92 | 89 |
| codex-sol-low | 76 | 71 | 72 |
| codex-oss | 282 | 219 | 239 |
| vibe-devstral | 199 | 143 | 156 |
| kimi-k31 | · | · | · |
| claude-opus | 106 | · | · |
| agy-oss | 236 | 71 | · |

## Runs that are not results, and key scrubbing

- n10-agy-oss-none-r3: exit 124 (timeout), 1200 s
- n10-agy-oss-none-r5: exit 124 (timeout), 1201 s
- n10-codex-oss-none-r1: exit 124 (timeout), 1203 s
- n6-vibe-devstral-none-r1: exit 3 (error), 453 s
- n6-vibe-devstral-none-r2: exit 3 (error), 676 s
- n6-vibe-devstral-none-r3: exit 3 (error), 607 s
- n6-vibe-devstral-none-r4: exit 3 (error), 462 s
- n6-vibe-devstral-story-r4: exit 3 (error), 426 s
- n6-vibe-devstral-story-r5: exit 3 (error), 403 s
- n6-vibe-devstral-ticket-r1: exit 3 (error), 514 s
- n6-vibe-devstral-ticket-r2: exit 3 (error), 619 s
- n6-vibe-devstral-ticket-r3: exit 3 (error), 475 s
- n6-vibe-devstral-ticket-r4: exit 3 (error), 427 s
- s8-codex-oss-none-r1: exit 124 (timeout), 1202 s
- s8-codex-oss-story-r4: exit 124 (timeout), 1201 s

Runs where the OpenRouter key was found and scrubbed: none
