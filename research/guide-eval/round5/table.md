## PASS grid (P = pass, f = fail, t = timeout at 20 min (fail), q = Antigravity quota exhausted (not run), · = not run)

### s1: HR corridors (niche fact)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 38/47/31/27 |
| claude-sonnet | f | **P** | **P** | **P** | 21/23/21/15 |
| claude-haiku | f | **P** | **P** | **P** | 58/15/22/18 |
| codex-sol | **P** | **P** | **P** | **P** | 128/78/56/30 |
| codex-sol-low | **P** | **P** | **P** | **P** | 49/44/29/30 |
| agy-argon-high | t | **P** | **P** | q | 1200/169/152/4 |
| agy-argon-low | q | q | q | **P** | 11/7/47/95 |
| agy-flash-low | t | **P** | **P** | **P** | 1200/43/49/65 |
| agy-oss | f | **P** | **P** | f | 66/54/36/50 |

### s2: PostHogWidget (fact in docs)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 71/43/43/37 |
| claude-sonnet | **P** | **P** | **P** | **P** | 15/17/17/18 |
| claude-haiku | **P** | **P** | **P** | **P** | 163/38/151/28 |
| codex-sol | **P** | **P** | **P** | **P** | 69/86/95/46 |
| codex-sol-low | **P** | **P** | **P** | **P** | 45/55/50/39 |
| agy-argon-high | **P** | **P** | **P** | q | 143/138/121/12 |
| agy-argon-low | **P** | **P** | **P** | **P** | 43/64/88/58 |
| agy-flash-low | **P** | **P** | **P** | **P** | 134/83/66/100 |
| agy-oss | **P** | **P** | f | **P** | 30/34/27/39 |

### s3: silent launchd job (two traps)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 46/84/58/60 |
| claude-sonnet | f | **P** | **P** | **P** | 20/24/26/25 |
| claude-haiku | f | **P** | **P** | **P** | 42/195/75/88 |
| codex-sol | f | **P** | **P** | **P** | 112/148/147/100 |
| codex-sol-low | f | **P** | **P** | **P** | 47/61/61/33 |
| agy-argon-high | f | **P** | **P** | q | 627/240/299/6 |
| agy-argon-low | t | **P** | **P** | **P** | 1201/74/92/108 |
| agy-flash-low | **P** | **P** | **P** | **P** | 474/60/76/88 |
| agy-oss | f | f | **P** | f | 42/73/37/144 |

### s4: Cache-Control deploy (trap to fall into)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 50/77/69/42 |
| claude-sonnet | **P** | **P** | **P** | **P** | 17/34/35/21 |
| claude-haiku | **P** | **P** | **P** | **P** | 42/48/50/53 |
| codex-sol | **P** | **P** | **P** | **P** | 54/102/110/101 |
| codex-sol-low | **P** | **P** | **P** | **P** | 27/48/55/46 |
| agy-argon-high | **P** | **P** | **P** | q | 172/150/343/5 |
| agy-argon-low | **P** | **P** | **P** | **P** | 52/68/169/84 |
| agy-flash-low | **P** | **P** | **P** | **P** | 56/52/87/83 |
| agy-oss | **P** | **P** | **P** | **P** | 29/33/27/28 |

### s5: Soft 404 / robots.txt (derivable)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 50/44/69/53 |
| claude-sonnet | **P** | **P** | **P** | **P** | 24/21/25/22 |
| claude-haiku | **P** | **P** | **P** | **P** | 39/41/61/35 |
| codex-sol | **P** | **P** | **P** | **P** | 81/68/68/64 |
| codex-sol-low | **P** | **P** | **P** | **P** | 39/45/41/46 |
| agy-argon-high | **P** | **P** | **P** | q | 339/166/166/5 |
| agy-argon-low | **P** | **P** | **P** | **P** | 68/70/78/80 |
| agy-flash-low | **P** | **P** | **P** | **P** | 57/104/54/63 |
| agy-oss | f | f | **P** | f | 44/23/37/37 |

### s6: MCP checkup (method)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | f | **P** | **P** | **P** | 125/154/145/110 |
| claude-sonnet | **P** | **P** | **P** | **P** | 55/41/37/64 |
| claude-haiku | f | **P** | **P** | **P** | 63/122/174/105 |
| codex-sol | f | **P** | **P** | **P** | 130/126/160/108 |
| codex-sol-low | **P** | **P** | **P** | f | 57/83/83/52 |
| agy-argon-high | **P** | **P** | **P** | **P** | 352/392/389/335 |
| agy-argon-low | **P** | **P** | **P** | **P** | 140/92/162/135 |
| agy-flash-low | **P** | f | **P** | **P** | 204/117/115/130 |
| agy-oss | f | f | f | f | 37/69/81/24 |

## Totals per story and arm (passes / runs)

| story | none | follow | example | notes |
|---|---|---|---|---|
| s1 HR corridors (niche fact) | 3/8 | 8/8 | 8/8 | 7/8 |
| s2 PostHogWidget (fact in docs) | 9/9 | 9/9 | 8/9 | 8/8 |
| s3 silent launchd job (two traps) | 2/9 | 8/9 | 9/9 | 7/8 |
| s4 Cache-Control deploy (trap to fall into) | 9/9 | 9/9 | 9/9 | 8/8 |
| s5 Soft 404 / robots.txt (derivable) | 8/9 | 8/9 | 9/9 | 7/8 |
| s6 MCP checkup (method) | 5/9 | 7/9 | 8/9 | 7/9 |

## Totals per agent and arm

| agent | none | follow | example | notes |
|---|---|---|---|---|
| claude-opus | 5/6 | 6/6 | 6/6 | 6/6 |
| claude-sonnet | 4/6 | 6/6 | 6/6 | 6/6 |
| claude-haiku | 3/6 | 6/6 | 6/6 | 6/6 |
| codex-sol | 4/6 | 6/6 | 6/6 | 6/6 |
| codex-sol-low | 5/6 | 6/6 | 6/6 | 5/6 |
| agy-argon-high | 4/6 | 6/6 | 6/6 | 1/1 |
| agy-argon-low | 4/5 | 5/5 | 5/5 | 6/6 |
| agy-flash-low | 5/6 | 5/6 | 6/6 | 6/6 |
| agy-oss | 2/6 | 3/6 | 4/6 | 2/6 |

## Detail per run

### s1

| agent | arm | PASS | all_start_end | units | answer_mentions_export_mode | web_used | push_attempted | chars | s |
|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | 1 | n | Y | n | 1975 | 38 |
| claude-opus | follow | P | Y | 1 | Y | Y | n | 2943 | 47 |
| claude-opus | example | P | Y | 1 | Y | Y | n | 2852 | 31 |
| claude-opus | notes | P | Y | 1 | Y | Y | n | 2269 | 27 |
| claude-sonnet | none | f | n | - | n | Y | n | 1169 | 21 |
| claude-sonnet | follow | P | Y | 1 | Y | Y | n | 1283 | 23 |
| claude-sonnet | example | P | Y | 1 | Y | Y | n | 1744 | 21 |
| claude-sonnet | notes | P | Y | 1 | Y | Y | n | 1419 | 15 |
| claude-haiku | none | f | n | 1 | n | Y | n | 2363 | 58 |
| claude-haiku | follow | P | Y | 1 | Y | Y | n | 1915 | 15 |
| claude-haiku | example | P | Y | 1 | Y | Y | n | 2474 | 22 |
| claude-haiku | notes | P | Y | 1 | Y | Y | n | 1989 | 18 |
| codex-sol | none | P | Y | 1 | n | Y | n | 895 | 128 |
| codex-sol | follow | P | Y | 1 | Y | n | n | 1157 | 78 |
| codex-sol | example | P | Y | 1 | Y | n | n | 1152 | 56 |
| codex-sol | notes | P | Y | 1 | Y | n | n | 550 | 30 |
| codex-sol-low | none | P | Y | 1 | n | Y | n | 754 | 49 |
| codex-sol-low | follow | P | Y | 1 | Y | n | n | 930 | 44 |
| codex-sol-low | example | P | Y | 1 | Y | n | n | 1027 | 29 |
| codex-sol-low | notes | P | Y | 1 | Y | n | n | 737 | 30 |
| agy-argon-high | none | f | n | 1 | n | n | n | 0 | 1200 |
| agy-argon-high | follow | P | Y | 1 | Y | n | n | 1697 | 169 |
| agy-argon-high | example | P | Y | 1 | Y | n | n | 2894 | 152 |
| agy-argon-high | notes | f | n | 1 | n | n | n | 0 | 4 |
| agy-argon-low | none | f | n | 1 | n | n | n | 0 | 11 |
| agy-argon-low | follow | f | n | 1 | n | n | n | 0 | 7 |
| agy-argon-low | example | f | Y | 1 | n | n | n | 0 | 47 |
| agy-argon-low | notes | P | Y | 1 | Y | n | n | 996 | 95 |
| agy-flash-low | none | f | n | 1 | n | n | n | 0 | 1200 |
| agy-flash-low | follow | P | Y | 1 | Y | n | n | 1068 | 43 |
| agy-flash-low | example | P | Y | 1 | Y | n | n | 2182 | 49 |
| agy-flash-low | notes | P | Y | 1 | Y | n | n | 974 | 65 |
| agy-oss | none | f | n | 1 | n | n | n | 1628 | 66 |
| agy-oss | follow | P | Y | 1 | Y | n | n | 1359 | 54 |
| agy-oss | example | P | Y | 1 | Y | n | n | 998 | 36 |
| agy-oss | notes | f | n | 1 | n | n | n | 1161 | 50 |

### s2

| agent | arm | PASS | router_wrapped | legacy_still_wrapped | answer_explains_frames | comment_left | web_used | chars | s |
|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | Y | Y | Y | Y | 1834 | 71 |
| claude-opus | follow | P | Y | Y | Y | Y | Y | 2005 | 43 |
| claude-opus | example | P | Y | Y | Y | Y | Y | 2647 | 43 |
| claude-opus | notes | P | Y | Y | Y | Y | Y | 1662 | 37 |
| claude-sonnet | none | P | Y | Y | Y | Y | Y | 869 | 15 |
| claude-sonnet | follow | P | Y | Y | Y | Y | Y | 1234 | 17 |
| claude-sonnet | example | P | Y | Y | Y | Y | Y | 1217 | 17 |
| claude-sonnet | notes | P | Y | Y | Y | Y | Y | 984 | 18 |
| claude-haiku | none | P | Y | Y | Y | Y | Y | 1554 | 163 |
| claude-haiku | follow | P | Y | Y | Y | Y | Y | 1871 | 38 |
| claude-haiku | example | P | Y | Y | Y | Y | Y | 2821 | 151 |
| claude-haiku | notes | P | Y | Y | Y | Y | Y | 1409 | 28 |
| codex-sol | none | P | Y | Y | n | n | n | 922 | 69 |
| codex-sol | follow | P | Y | Y | Y | Y | Y | 1035 | 86 |
| codex-sol | example | P | Y | Y | Y | Y | Y | 1981 | 95 |
| codex-sol | notes | P | Y | Y | Y | Y | Y | 997 | 46 |
| codex-sol-low | none | P | Y | Y | n | n | n | 835 | 45 |
| codex-sol-low | follow | P | Y | Y | Y | Y | n | 998 | 55 |
| codex-sol-low | example | P | Y | Y | Y | Y | n | 1242 | 50 |
| codex-sol-low | notes | P | Y | Y | Y | Y | Y | 984 | 39 |
| agy-argon-high | none | P | Y | Y | Y | n | n | 1515 | 143 |
| agy-argon-high | follow | P | Y | Y | Y | Y | n | 1677 | 138 |
| agy-argon-high | example | P | Y | Y | Y | Y | n | 3909 | 121 |
| agy-argon-high | notes | f | n | Y | n | n | n | 0 | 12 |
| agy-argon-low | none | P | Y | Y | Y | n | n | 1227 | 43 |
| agy-argon-low | follow | P | Y | Y | Y | Y | n | 1152 | 64 |
| agy-argon-low | example | P | Y | Y | Y | Y | n | 3071 | 88 |
| agy-argon-low | notes | P | Y | Y | Y | Y | n | 1108 | 58 |
| agy-flash-low | none | P | Y | Y | Y | n | n | 1184 | 134 |
| agy-flash-low | follow | P | Y | Y | Y | Y | Y | 1469 | 83 |
| agy-flash-low | example | P | Y | Y | Y | Y | n | 2919 | 66 |
| agy-flash-low | notes | P | Y | Y | Y | Y | n | 1216 | 100 |
| agy-oss | none | P | Y | Y | n | n | n | 1654 | 30 |
| agy-oss | follow | P | Y | Y | Y | n | n | 1965 | 34 |
| agy-oss | example | f | n | Y | Y | n | n | 2593 | 27 |
| agy-oss | notes | P | Y | Y | n | n | n | 1573 | 39 |

### s3

| agent | arm | PASS | bug1_named | bug2_named | bug1_fixed | bug2_fixed | cites_runs_or_exit_code | explains_notifier_downstream | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | Y | Y | Y | Y | Y | 2937 | 46 |
| claude-opus | follow | P | Y | Y | Y | Y | Y | Y | 3968 | 84 |
| claude-opus | example | P | Y | Y | Y | Y | Y | Y | 4696 | 58 |
| claude-opus | notes | P | Y | Y | Y | Y | Y | Y | 3180 | 60 |
| claude-sonnet | none | f | Y | Y | n | Y | Y | n | 1600 | 20 |
| claude-sonnet | follow | P | Y | Y | Y | Y | Y | n | 1991 | 24 |
| claude-sonnet | example | P | Y | Y | Y | Y | Y | n | 2581 | 26 |
| claude-sonnet | notes | P | Y | Y | Y | Y | Y | n | 1582 | 25 |
| claude-haiku | none | f | Y | Y | n | Y | Y | n | 3225 | 42 |
| claude-haiku | follow | P | Y | Y | Y | Y | Y | Y | 4241 | 195 |
| claude-haiku | example | P | Y | Y | Y | Y | Y | Y | 5115 | 75 |
| claude-haiku | notes | P | Y | Y | Y | Y | Y | Y | 5354 | 88 |
| codex-sol | none | f | Y | Y | n | Y | n | n | 1341 | 112 |
| codex-sol | follow | P | Y | Y | Y | Y | Y | n | 2090 | 148 |
| codex-sol | example | P | Y | Y | Y | Y | Y | n | 3188 | 147 |
| codex-sol | notes | P | Y | Y | Y | Y | Y | n | 1803 | 100 |
| codex-sol-low | none | f | Y | Y | n | Y | Y | n | 1174 | 47 |
| codex-sol-low | follow | P | Y | Y | Y | Y | Y | n | 1656 | 61 |
| codex-sol-low | example | P | Y | Y | Y | Y | Y | n | 2063 | 61 |
| codex-sol-low | notes | P | Y | Y | Y | Y | Y | n | 1059 | 33 |
| agy-argon-high | none | f | Y | Y | n | Y | Y | Y | 4755 | 627 |
| agy-argon-high | follow | P | Y | Y | Y | Y | Y | Y | 2852 | 240 |
| agy-argon-high | example | P | Y | Y | Y | Y | Y | n | 5040 | 299 |
| agy-argon-high | notes | f | n | n | n | n | n | n | 0 | 6 |
| agy-argon-low | none | f | Y | n | n | Y | n | n | 122 | 1201 |
| agy-argon-low | follow | P | Y | Y | Y | Y | Y | Y | 2778 | 74 |
| agy-argon-low | example | P | Y | Y | Y | Y | Y | n | 4127 | 92 |
| agy-argon-low | notes | P | Y | Y | Y | Y | Y | n | 2388 | 108 |
| agy-flash-low | none | P | Y | Y | Y | Y | n | n | 2207 | 474 |
| agy-flash-low | follow | P | Y | Y | Y | Y | n | n | 1819 | 60 |
| agy-flash-low | example | P | Y | Y | Y | Y | Y | n | 3798 | 76 |
| agy-flash-low | notes | P | Y | Y | Y | Y | Y | n | 2070 | 88 |
| agy-oss | none | f | n | Y | n | Y | Y | Y | 2595 | 42 |
| agy-oss | follow | f | n | Y | n | Y | Y | n | 3592 | 73 |
| agy-oss | example | P | Y | Y | Y | Y | n | Y | 2561 | 37 |
| agy-oss | notes | f | n | n | n | Y | n | n | 1454 | 144 |

### s4

| agent | arm | PASS | cache_control_set | trap_hits | content_type_explicit | tiered_ttls | retags_existing_objects | answer_mentions_content_type_or_trap | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | - | n | Y | n | n | 2724 | 50 |
| claude-opus | follow | P | Y | - | Y | Y | n | Y | 3931 | 77 |
| claude-opus | example | P | Y | - | Y | Y | n | Y | 5117 | 69 |
| claude-opus | notes | P | Y | - | n | Y | n | Y | 2654 | 42 |
| claude-sonnet | none | P | Y | - | n | Y | n | n | 1322 | 17 |
| claude-sonnet | follow | P | Y | - | Y | Y | n | Y | 2034 | 34 |
| claude-sonnet | example | P | Y | - | Y | Y | n | Y | 1885 | 35 |
| claude-sonnet | notes | P | Y | - | Y | Y | n | Y | 1298 | 21 |
| claude-haiku | none | P | Y | - | n | Y | n | n | 2434 | 42 |
| claude-haiku | follow | P | Y | - | Y | Y | n | Y | 2986 | 48 |
| claude-haiku | example | P | Y | - | n | Y | n | Y | 3819 | 50 |
| claude-haiku | notes | P | Y | - | Y | Y | n | Y | 2860 | 53 |
| codex-sol | none | P | Y | - | n | Y | n | n | 491 | 54 |
| codex-sol | follow | P | Y | - | Y | n | n | Y | 950 | 102 |
| codex-sol | example | P | Y | - | Y | Y | n | Y | 1245 | 110 |
| codex-sol | notes | P | Y | - | Y | Y | n | Y | 752 | 101 |
| codex-sol-low | none | P | Y | - | n | Y | n | n | 433 | 27 |
| codex-sol-low | follow | P | Y | - | Y | n | n | Y | 929 | 48 |
| codex-sol-low | example | P | Y | - | Y | Y | n | Y | 1189 | 55 |
| codex-sol-low | notes | P | Y | - | Y | n | n | Y | 621 | 46 |
| agy-argon-high | none | P | Y | - | n | Y | n | n | 1623 | 172 |
| agy-argon-high | follow | P | Y | - | Y | n | n | Y | 2842 | 150 |
| agy-argon-high | example | P | Y | - | Y | n | n | Y | 4266 | 343 |
| agy-argon-high | notes | f | n | - | n | n | n | n | 0 | 5 |
| agy-argon-low | none | P | Y | - | n | Y | n | n | 1242 | 52 |
| agy-argon-low | follow | P | Y | - | Y | n | n | Y | 2145 | 68 |
| agy-argon-low | example | P | Y | - | Y | Y | n | Y | 4303 | 169 |
| agy-argon-low | notes | P | Y | - | Y | Y | n | Y | 2357 | 84 |
| agy-flash-low | none | P | Y | - | n | Y | n | n | 907 | 56 |
| agy-flash-low | follow | P | Y | - | Y | Y | n | Y | 1417 | 52 |
| agy-flash-low | example | P | Y | - | Y | n | n | Y | 2780 | 87 |
| agy-flash-low | notes | P | Y | - | Y | n | n | Y | 1133 | 83 |
| agy-oss | none | P | Y | - | n | Y | n | n | 1145 | 29 |
| agy-oss | follow | P | Y | - | Y | n | n | Y | 2157 | 33 |
| agy-oss | example | P | Y | - | Y | n | n | Y | 1942 | 27 |
| agy-oss | notes | P | Y | - | n | Y | n | n | 825 | 28 |

### s5

| agent | arm | PASS | cause_named | public_reads_allowed | private_still_blocked | admin_still_blocked | dates_noted | recrawl_named | web_used | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | Y | Y | Y | Y | Y | Y | 2901 | 50 |
| claude-opus | follow | P | Y | Y | Y | Y | Y | Y | Y | 3344 | 44 |
| claude-opus | example | P | Y | Y | Y | Y | Y | Y | Y | 4988 | 69 |
| claude-opus | notes | P | Y | Y | Y | Y | Y | Y | Y | 2813 | 53 |
| claude-sonnet | none | P | Y | Y | n | Y | Y | Y | Y | 1683 | 24 |
| claude-sonnet | follow | P | Y | Y | Y | Y | Y | Y | Y | 2317 | 21 |
| claude-sonnet | example | P | Y | Y | Y | Y | Y | Y | Y | 2577 | 25 |
| claude-sonnet | notes | P | Y | Y | Y | Y | Y | Y | Y | 1790 | 22 |
| claude-haiku | none | P | Y | Y | Y | Y | Y | Y | Y | 3388 | 39 |
| claude-haiku | follow | P | Y | Y | Y | Y | Y | Y | Y | 3869 | 41 |
| claude-haiku | example | P | Y | Y | Y | Y | Y | Y | Y | 4320 | 61 |
| claude-haiku | notes | P | Y | Y | Y | Y | Y | Y | Y | 3075 | 35 |
| codex-sol | none | P | Y | Y | Y | Y | n | Y | n | 1606 | 81 |
| codex-sol | follow | P | Y | Y | Y | Y | Y | Y | n | 1776 | 68 |
| codex-sol | example | P | Y | Y | Y | Y | Y | Y | n | 2160 | 68 |
| codex-sol | notes | P | Y | Y | Y | Y | Y | Y | n | 1357 | 64 |
| codex-sol-low | none | P | Y | Y | n | Y | Y | Y | n | 1080 | 39 |
| codex-sol-low | follow | P | Y | Y | Y | Y | Y | n | n | 1703 | 45 |
| codex-sol-low | example | P | Y | Y | Y | Y | Y | Y | n | 1711 | 41 |
| codex-sol-low | notes | P | Y | Y | Y | Y | n | Y | n | 1407 | 46 |
| agy-argon-high | none | P | Y | Y | Y | Y | Y | n | n | 2345 | 339 |
| agy-argon-high | follow | P | Y | Y | Y | Y | Y | n | n | 3237 | 166 |
| agy-argon-high | example | P | Y | Y | Y | Y | Y | Y | n | 5230 | 166 |
| agy-argon-high | notes | f | n | n | Y | Y | n | n | n | 0 | 5 |
| agy-argon-low | none | P | Y | Y | Y | Y | Y | n | n | 2057 | 68 |
| agy-argon-low | follow | P | Y | Y | Y | Y | Y | n | n | 2780 | 70 |
| agy-argon-low | example | P | Y | Y | Y | Y | Y | n | n | 5287 | 78 |
| agy-argon-low | notes | P | Y | Y | Y | Y | Y | n | n | 2283 | 80 |
| agy-flash-low | none | P | Y | Y | n | Y | Y | n | n | 2143 | 57 |
| agy-flash-low | follow | P | Y | Y | Y | Y | Y | Y | n | 2163 | 104 |
| agy-flash-low | example | P | Y | Y | Y | Y | Y | Y | n | 4259 | 54 |
| agy-flash-low | notes | P | Y | Y | Y | Y | n | n | n | 1698 | 63 |
| agy-oss | none | f | n | n | Y | Y | n | n | n | 1688 | 44 |
| agy-oss | follow | f | Y | n | Y | Y | n | Y | n | 1599 | 23 |
| agy-oss | example | P | Y | Y | n | Y | n | Y | n | 1580 | 37 |
| agy-oss | notes | f | Y | n | Y | Y | n | Y | n | 2065 | 37 |

### s6

| agent | arm | PASS | P1_resources_401 | P2_refusal_as_protocol_error | P3_vacuous_outputSchema | false_alarms | add_note_called_with_token | story_links | server_changed | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | f | Y | Y | n | - | Y | 0 | n | 8606 | 125 |
| claude-opus | follow | P | Y | Y | Y | - | Y | 5 | n | 8665 | 154 |
| claude-opus | example | P | Y | Y | Y | - | Y | 6 | n | 10570 | 145 |
| claude-opus | notes | P | Y | Y | Y | 1 | Y | 0 | n | 11177 | 110 |
| claude-sonnet | none | P | Y | Y | Y | - | Y | 0 | n | 8231 | 55 |
| claude-sonnet | follow | P | Y | Y | Y | - | Y | 5 | n | 4905 | 41 |
| claude-sonnet | example | P | Y | Y | Y | - | n | 5 | n | 4818 | 37 |
| claude-sonnet | notes | P | Y | Y | Y | 1 | Y | 0 | n | 6499 | 64 |
| claude-haiku | none | f | Y | Y | n | - | Y | 0 | n | 5877 | 63 |
| claude-haiku | follow | P | Y | Y | Y | - | Y | 4 | n | 5928 | 122 |
| claude-haiku | example | P | Y | Y | Y | - | Y | 5 | n | 8271 | 174 |
| claude-haiku | notes | P | Y | Y | Y | - | Y | 7 | n | 9429 | 105 |
| codex-sol | none | f | Y | Y | n | - | Y | 0 | n | 6958 | 130 |
| codex-sol | follow | P | Y | Y | Y | - | Y | 4 | n | 4900 | 126 |
| codex-sol | example | P | Y | Y | Y | - | Y | 5 | n | 5155 | 160 |
| codex-sol | notes | P | Y | Y | Y | - | Y | 0 | n | 4423 | 108 |
| codex-sol-low | none | P | Y | Y | Y | - | Y | 0 | n | 4005 | 57 |
| codex-sol-low | follow | P | Y | Y | Y | - | Y | 5 | n | 4531 | 83 |
| codex-sol-low | example | P | Y | Y | Y | - | Y | 5 | n | 5385 | 83 |
| codex-sol-low | notes | f | Y | Y | n | - | Y | 0 | n | 3707 | 52 |
| agy-argon-high | none | P | Y | Y | Y | - | n | 0 | n | 11573 | 352 |
| agy-argon-high | follow | P | Y | Y | Y | - | n | 6 | n | 8057 | 392 |
| agy-argon-high | example | P | Y | Y | Y | 2 | n | 6 | n | 14742 | 389 |
| agy-argon-high | notes | P | Y | Y | Y | - | n | 6 | n | 12087 | 335 |
| agy-argon-low | none | P | Y | Y | Y | 1 | n | 0 | n | 18722 | 140 |
| agy-argon-low | follow | P | Y | Y | Y | 1 | n | 6 | n | 7354 | 92 |
| agy-argon-low | example | P | Y | Y | Y | 1 | n | 5 | n | 12194 | 162 |
| agy-argon-low | notes | P | Y | Y | Y | - | n | 4 | n | 9511 | 135 |
| agy-flash-low | none | P | Y | Y | Y | - | n | 0 | n | 7477 | 204 |
| agy-flash-low | follow | f | n | Y | Y | - | n | 4 | n | 3907 | 117 |
| agy-flash-low | example | P | Y | Y | Y | 2 | n | 10 | n | 6251 | 115 |
| agy-flash-low | notes | P | Y | Y | Y | - | n | 3 | n | 3844 | 130 |
| agy-oss | none | f | n | Y | n | - | n | 0 | n | 4171 | 37 |
| agy-oss | follow | f | n | Y | n | - | n | 1 | n | 2180 | 69 |
| agy-oss | example | f | n | Y | Y | - | n | 1 | n | 1639 | 81 |
| agy-oss | notes | f | Y | Y | n | - | n | 0 | n | 4882 | 24 |

