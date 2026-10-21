## PASS grid (P = pass, f = fail, t = timeout at 20 min (fail), q = quota exhausted (not run), · = not run)

### s7: Intervals OAuth quirks (niche fact)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 100/101/85/120 |
| claude-sonnet | f | **P** | **P** | **P** | 32/36/26/30 |
| claude-haiku | f | **P** | **P** | **P** | 81/118/140/78 |
| codex-sol | **P** | **P** | **P** | **P** | 94/98/93/75 |
| codex-sol-low | **P** | **P** | **P** | **P** | 74/53/54/70 |
| agy-flash-low | f | **P** | **P** | **P** | 436/137/178/106 |
| agy-oss | t | f | f | f | 1200/245/88/35 |

### s8: two cache_control segments (fact in docs)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 139/86/142/137 |
| claude-sonnet | **P** | **P** | **P** | **P** | 27/26/19/25 |
| claude-haiku | **P** | **P** | **P** | **P** | 48/43/55/64 |
| codex-sol | **P** | **P** | **P** | **P** | 117/55/78/54 |
| codex-sol-low | **P** | **P** | **P** | **P** | 58/21/29/25 |
| agy-flash-low | **P** | **P** | **P** | **P** | 282/59/48/57 |
| agy-oss | f | **P** | **P** | f | 26/49/40/37 |

### s9: DynamoDB reserved words (two bugs, one silent)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 58/71/73/70 |
| claude-sonnet | **P** | **P** | **P** | **P** | 30/25/31/24 |
| claude-haiku | **P** | **P** | **P** | **P** | 68/78/86/57 |
| codex-sol | **P** | **P** | **P** | **P** | 46/42/49/46 |
| codex-sol-low | **P** | **P** | **P** | **P** | 21/34/33/22 |
| agy-flash-low | **P** | **P** | **P** | **P** | 86/68/68/65 |
| agy-oss | f | **P** | **P** | f | 32/50/42/36 |

### s10: PostHog event per keystroke (trap to fall into)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 57/49/62/85 |
| claude-sonnet | **P** | **P** | **P** | **P** | 30/21/22/18 |
| claude-haiku | **P** | **P** | **P** | **P** | 58/49/52/50 |
| codex-sol | f | **P** | **P** | **P** | 80/64/61/69 |
| codex-sol-low | f | **P** | **P** | **P** | 47/38/45/54 |
| agy-flash-low | **P** | **P** | **P** | **P** | 847/82/86/73 |
| agy-oss | f | f | f | f | 291/252/100/194 |

### s11: crash on the second write (derivable)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 37/47/45/43 |
| claude-sonnet | **P** | **P** | **P** | **P** | 27/26/21/26 |
| claude-haiku | **P** | **P** | **P** | **P** | 27/35/44/41 |
| codex-sol | **P** | **P** | **P** | **P** | 38/37/52/44 |
| codex-sol-low | **P** | **P** | **P** | **P** | 26/24/34/25 |
| agy-flash-low | **P** | **P** | **P** | **P** | 56/99/64/107 |
| agy-oss | **P** | **P** | **P** | **P** | 23/29/31/24 |

### s12: two-account authorization test (method)

| agent | none | follow | example | notes | time none/follow/example/notes |
|---|---|---|---|---|---|
| claude-opus | **P** | **P** | **P** | **P** | 75/86/78/76 |
| claude-sonnet | **P** | **P** | **P** | **P** | 20/37/33/28 |
| claude-haiku | **P** | **P** | **P** | **P** | 40/78/59/48 |
| codex-sol | **P** | **P** | **P** | **P** | 55/84/69/59 |
| codex-sol-low | **P** | **P** | **P** | **P** | 35/49/38/36 |
| agy-flash-low | **P** | **P** | **P** | **P** | 112/100/94/99 |
| agy-oss | f | **P** | **P** | **P** | 31/53/48/24 |

## Totals per story and arm (passes / runs)

| | none | follow | example | notes |
|---|---|---|---|---|
| s7 Intervals OAuth quirks (niche fact) | 3/7 | 6/7 | 6/7 | 6/7 |
| s8 two cache_control segments (fact in docs) | 6/7 | 7/7 | 7/7 | 6/7 |
| s9 DynamoDB reserved words (two bugs, one silent) | 6/7 | 7/7 | 7/7 | 6/7 |
| s10 PostHog event per keystroke (trap to fall into) | 4/7 | 6/7 | 6/7 | 6/7 |
| s11 crash on the second write (derivable) | 7/7 | 7/7 | 7/7 | 7/7 |
| s12 two-account authorization test (method) | 6/7 | 7/7 | 7/7 | 7/7 |

## Totals per agent and arm

| | none | follow | example | notes |
|---|---|---|---|---|
| claude-opus  | 6/6 | 6/6 | 6/6 | 6/6 |
| claude-sonnet  | 5/6 | 6/6 | 6/6 | 6/6 |
| claude-haiku  | 5/6 | 6/6 | 6/6 | 6/6 |
| codex-sol  | 5/6 | 6/6 | 6/6 | 6/6 |
| codex-sol-low  | 5/6 | 6/6 | 6/6 | 6/6 |
| agy-flash-low  | 5/6 | 6/6 | 6/6 | 6/6 |
| agy-oss  | 1/6 | 4/6 | 4/6 | 2/6 |

## Detail per run (every boolean or list field of the grade, in the grader's order)

### s7

| agent | arm | PASS | answer_file | py_parse_errors | scope_strings | scope_dup_areas | scope_fixed | scope_no_read_with_write(bonus) | refresh_idents_left | refresh_job_idents_left | expiry_idents_left | refresh_machinery_removed(info) | live_server_started | live_init | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | - | 1 | - | Y | Y | 4 | 3 | 2 | n | Y | 2 | 4330 | 100 |
| claude-opus | follow | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 4844 | 101 |
| claude-opus | example | P | Y | - | 1 | - | Y | Y | 4 | 3 | 2 | n | Y | 2 | 5556 | 85 |
| claude-opus | notes | P | Y | - | 1 | - | Y | Y | 3 | 2 | 3 | n | Y | 2 | 3624 | 120 |
| claude-sonnet | none | f | Y | - | 1 | 1 | n | n | 4 | 3 | 2 | n | Y | 2 | 1742 | 32 |
| claude-sonnet | follow | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 1824 | 36 |
| claude-sonnet | example | P | Y | - | 1 | - | Y | Y | 4 | 3 | 2 | n | Y | 2 | 2209 | 26 |
| claude-sonnet | notes | P | Y | - | 1 | - | Y | Y | 4 | 3 | 3 | n | Y | 2 | 1528 | 30 |
| claude-haiku | none | f | Y | - | 1 | 2 | n | n | 4 | 3 | 3 | n | Y | 2 | 3560 | 81 |
| claude-haiku | follow | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 5336 | 118 |
| claude-haiku | example | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 6809 | 140 |
| claude-haiku | notes | P | Y | - | 1 | - | Y | Y | 4 | 3 | 3 | n | Y | 2 | 4394 | 78 |
| codex-sol | none | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 1717 | 94 |
| codex-sol | follow | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 1555 | 98 |
| codex-sol | example | P | Y | - | 1 | - | Y | Y | - | - | 1 | n | Y | 2 | 3257 | 93 |
| codex-sol | notes | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 1666 | 75 |
| codex-sol-low | none | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 1284 | 74 |
| codex-sol-low | follow | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 1209 | 53 |
| codex-sol-low | example | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 1747 | 54 |
| codex-sol-low | notes | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 1409 | 70 |
| agy-flash-low | none | f | Y | - | 1 | 2 | n | n | 4 | 3 | 2 | n | Y | 2 | 2303 | 436 |
| agy-flash-low | follow | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 2777 | 137 |
| agy-flash-low | example | P | Y | - | 1 | - | Y | Y | - | - | - | Y | Y | 2 | 3884 | 178 |
| agy-flash-low | notes | P | Y | - | 1 | - | Y | Y | 3 | 2 | 2 | n | Y | 2 | 2633 | 106 |
| agy-oss | none | f | n | - | 1 | 2 | n | n | 4 | 3 | 3 | n | Y | 2 | 2590 | 1200 |
| agy-oss | follow | f | n | - | 1 | - | Y | Y | 4 | 3 | 3 | n | Y | 2 | 1015 | 245 |
| agy-oss | example | f | n | - | 1 | - | Y | Y | 4 | 3 | 3 | n | Y | 2 | 2474 | 88 |
| agy-oss | notes | f | Y | - | 1 | - | Y | Y | 4 | 3 | 3 | n | Y | 2 | 1023 | 35 |

### s8

| agent | arm | PASS | answer_file | memory_write_keeps_instructions_cached | probe_saw_the_new_fact | shared_prefix_across_athletes(info) | static_holds_instructions | static_marked | static_independent_of_facts_and_date | first_block_differs_between_users | tail_after_static | tail_marked | tools_changed | tools_marker_in_source | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | Y | Y | n | n | n | n | Y | Y | Y | n | n | 3426 | 139 |
| claude-opus | follow | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 3294 | 86 |
| claude-opus | example | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 5303 | 142 |
| claude-opus | notes | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 4325 | 137 |
| claude-sonnet | none | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 1693 | 27 |
| claude-sonnet | follow | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 1768 | 26 |
| claude-sonnet | example | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 1673 | 19 |
| claude-sonnet | notes | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 1374 | 25 |
| claude-haiku | none | P | Y | Y | Y | Y | Y | Y | Y | n | Y | n | n | n | 2801 | 48 |
| claude-haiku | follow | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 3205 | 43 |
| claude-haiku | example | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 4016 | 55 |
| claude-haiku | notes | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 3221 | 64 |
| codex-sol | none | P | Y | Y | Y | Y | Y | Y | Y | n | Y | n | n | n | 1642 | 117 |
| codex-sol | follow | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 1102 | 55 |
| codex-sol | example | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 2097 | 78 |
| codex-sol | notes | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 574 | 54 |
| codex-sol-low | none | P | Y | Y | Y | n | n | n | n | Y | Y | n | n | n | 656 | 58 |
| codex-sol-low | follow | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 737 | 21 |
| codex-sol-low | example | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 1063 | 29 |
| codex-sol-low | notes | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 829 | 25 |
| agy-flash-low | none | P | Y | Y | Y | Y | Y | Y | Y | n | Y | n | n | n | 1818 | 282 |
| agy-flash-low | follow | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 1865 | 59 |
| agy-flash-low | example | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 2682 | 48 |
| agy-flash-low | notes | P | Y | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 1510 | 57 |
| agy-oss | none | f | n | n | Y | n | Y | n | Y | n | Y | Y | n | n | 966 | 26 |
| agy-oss | follow | P | n | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 2939 | 49 |
| agy-oss | example | P | n | Y | Y | Y | Y | Y | Y | n | Y | Y | n | n | 967 | 40 |
| agy-oss | notes | f | n | n | Y | n | Y | n | Y | n | Y | Y | n | n | 1323 | 37 |

### s9

| agent | arm | PASS | answer_file | bug1_named | bug2_named | latent_named | blanket_rule_named | bare_reserved_left | update_bare_hidden_left | projection_bare_left | bug1_fixed | bug2_fixed | blanket | seeded_test | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 3607 | 58 |
| claude-opus | follow | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 3250 | 71 |
| claude-opus | example | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 4548 | 73 |
| claude-opus | notes | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 4154 | 70 |
| claude-sonnet | none | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | Y | 1570 | 30 |
| claude-sonnet | follow | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 1359 | 25 |
| claude-sonnet | example | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 2330 | 31 |
| claude-sonnet | notes | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 1280 | 24 |
| claude-haiku | none | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 3484 | 68 |
| claude-haiku | follow | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 3518 | 78 |
| claude-haiku | example | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 5228 | 86 |
| claude-haiku | notes | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 3433 | 57 |
| codex-sol | none | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 1055 | 46 |
| codex-sol | follow | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 1218 | 42 |
| codex-sol | example | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 2128 | 49 |
| codex-sol | notes | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 1150 | 46 |
| codex-sol-low | none | P | Y | Y | Y | n | Y | 1 | - | - | Y | Y | n | n | 784 | 21 |
| codex-sol-low | follow | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 1249 | 34 |
| codex-sol-low | example | P | Y | Y | Y | n | Y | - | - | - | Y | Y | Y | n | 1518 | 33 |
| codex-sol-low | notes | P | Y | Y | Y | n | n | 1 | - | - | Y | Y | n | n | 718 | 22 |
| agy-flash-low | none | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 1646 | 86 |
| agy-flash-low | follow | P | Y | Y | Y | n | Y | - | - | - | Y | Y | Y | Y | 2096 | 68 |
| agy-flash-low | example | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 3637 | 68 |
| agy-flash-low | notes | P | Y | Y | Y | Y | Y | - | - | - | Y | Y | Y | n | 2333 | 65 |
| agy-oss | none | f | n | Y | n | n | Y | 2 | - | 1 | Y | n | n | n | 1821 | 32 |
| agy-oss | follow | P | Y | Y | Y | n | Y | 1 | - | - | Y | Y | n | n | 2240 | 50 |
| agy-oss | example | P | n | Y | Y | n | Y | 1 | - | - | Y | Y | n | n | 2213 | 42 |
| agy-oss | notes | f | n | Y | n | n | Y | 2 | - | 1 | Y | n | n | n | 1859 | 36 |

### s10

| agent | arm | PASS | answer_file | all_events_implemented | trap_hits | on_change_end_used | once_flag_used | focus_lost_used | submit_or_editing_complete_used | scroll_end_used | scroll_update_mentioned | answer_mentions_keystroke_quota_once | flutter_or_dart_executed | changed_files | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 2982 | 57 |
| claude-opus | follow | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 2989 | 49 |
| claude-opus | example | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 4204 | 62 |
| claude-opus | notes | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 2459 | 85 |
| claude-sonnet | none | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 1074 | 30 |
| claude-sonnet | follow | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 1101 | 21 |
| claude-sonnet | example | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 1552 | 22 |
| claude-sonnet | notes | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 1094 | 18 |
| claude-haiku | none | P | Y | Y | - | Y | Y | n | n | Y | n | Y | Y | 3 | 2586 | 58 |
| claude-haiku | follow | P | Y | Y | - | Y | Y | n | n | Y | n | Y | Y | 3 | 3003 | 49 |
| claude-haiku | example | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 3707 | 52 |
| claude-haiku | notes | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 3093 | 50 |
| codex-sol | none | f | Y | Y | 1 | n | Y | n | n | Y | Y | Y | n | 3 | 1014 | 80 |
| codex-sol | follow | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 776 | 64 |
| codex-sol | example | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 1447 | 61 |
| codex-sol | notes | P | Y | Y | - | Y | Y | n | n | Y | Y | Y | n | 3 | 723 | 69 |
| codex-sol-low | none | f | Y | Y | 1 | n | Y | n | n | Y | Y | Y | n | 3 | 597 | 47 |
| codex-sol-low | follow | P | Y | Y | - | Y | Y | n | n | Y | n | n | n | 3 | 746 | 38 |
| codex-sol-low | example | P | Y | Y | - | Y | Y | n | n | Y | n | Y | n | 3 | 1010 | 45 |
| codex-sol-low | notes | P | Y | Y | - | Y | Y | n | n | Y | Y | Y | n | 3 | 661 | 54 |
| agy-flash-low | none | P | Y | Y | - | Y | Y | n | n | Y | n | Y | Y | 8 | 1813 | 847 |
| agy-flash-low | follow | P | Y | Y | - | Y | Y | n | n | Y | n | Y | Y | 7 | 1634 | 82 |
| agy-flash-low | example | P | Y | Y | - | Y | Y | n | n | Y | n | Y | Y | 7 | 3707 | 86 |
| agy-flash-low | notes | P | Y | Y | - | Y | Y | n | n | Y | n | Y | Y | 7 | 1783 | 73 |
| agy-oss | none | f | n | n | 1 | n | Y | n | n | n | n | n | n | 1 | 636 | 291 |
| agy-oss | follow | f | n | n | - | Y | Y | n | n | n | n | Y | n | 2 | 1312 | 252 |
| agy-oss | example | f | n | n | - | Y | Y | n | n | Y | n | Y | n | 2 | 2417 | 100 |
| agy-oss | notes | f | n | n | - | n | Y | n | n | n | n | n | n | 1 | 579 | 194 |

### s11

| agent | arm | PASS | answer_file | cause_named | explains_empty_path | fix_named | hidden_first_ok | hidden_second_ok | similar_stored | score_types | scoring_kept | seeded_test | seeded_test_in | ran_tests | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 2210 | 37 |
| claude-opus | follow | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | Y | 2202 | 47 |
| claude-opus | example | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 2477 | 45 |
| claude-opus | notes | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 1914 | 43 |
| claude-sonnet | none | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | Y | 1050 | 27 |
| claude-sonnet | follow | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 1257 | 26 |
| claude-sonnet | example | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 2 | Y | 1584 | 21 |
| claude-sonnet | notes | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 1162 | 26 |
| claude-haiku | none | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 2 | Y | 1536 | 27 |
| claude-haiku | follow | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 2 | Y | 2151 | 35 |
| claude-haiku | example | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 4151 | 44 |
| claude-haiku | notes | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 2 | Y | 1902 | 41 |
| codex-sol | none | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | Y | 827 | 38 |
| codex-sol | follow | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 925 | 37 |
| codex-sol | example | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | Y | 1457 | 52 |
| codex-sol | notes | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 788 | 44 |
| codex-sol-low | none | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 683 | 26 |
| codex-sol-low | follow | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 841 | 24 |
| codex-sol-low | example | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | Y | 1556 | 34 |
| codex-sol-low | notes | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | Y | 799 | 25 |
| agy-flash-low | none | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 2 | Y | 1543 | 56 |
| agy-flash-low | follow | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 2 | Y | 2042 | 99 |
| agy-flash-low | example | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 1 | Y | 2513 | 64 |
| agy-flash-low | notes | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | Y | 2 | Y | 2686 | 107 |
| agy-oss | none | P | n | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | n | 1223 | 23 |
| agy-oss | follow | P | n | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | Y | 1632 | 29 |
| agy-oss | example | P | n | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | n | 2036 | 31 |
| agy-oss | notes | P | Y | Y | Y | Y | Y | Y | 1 | 1 | Y | n | - | Y | 1609 | 24 |

### s12

| agent | arm | PASS | killed_before_start | server_started | answer_file | gaps_closed | other_endpoints_closed | regression | named_like | named_view | false_positives | two_accounts | probed_like | probed_view | chars | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus | none | P | - | Y | Y | Y | Y | n | Y | Y | 1 | Y | Y | Y | 4184 | 75 |
| claude-opus | follow | P | - | Y | Y | Y | Y | n | Y | Y | 1 | Y | Y | Y | 4222 | 86 |
| claude-opus | example | P | - | Y | Y | Y | Y | n | Y | Y | 1 | Y | Y | Y | 5229 | 78 |
| claude-opus | notes | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 2961 | 76 |
| claude-sonnet | none | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 1323 | 20 |
| claude-sonnet | follow | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 1651 | 37 |
| claude-sonnet | example | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 2550 | 33 |
| claude-sonnet | notes | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 1493 | 28 |
| claude-haiku | none | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 3462 | 40 |
| claude-haiku | follow | P | - | Y | Y | Y | Y | n | Y | Y | 1 | Y | Y | Y | 4111 | 78 |
| claude-haiku | example | P | - | Y | Y | Y | Y | n | Y | Y | 1 | Y | Y | Y | 5674 | 59 |
| claude-haiku | notes | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 3902 | 48 |
| codex-sol | none | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 1661 | 55 |
| codex-sol | follow | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 3137 | 84 |
| codex-sol | example | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 2103 | 69 |
| codex-sol | notes | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 1307 | 59 |
| codex-sol-low | none | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 1054 | 35 |
| codex-sol-low | follow | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 1714 | 49 |
| codex-sol-low | example | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 1549 | 38 |
| codex-sol-low | notes | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 1075 | 36 |
| agy-flash-low | none | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 3500 | 112 |
| agy-flash-low | follow | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 3917 | 100 |
| agy-flash-low | example | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 5129 | 94 |
| agy-flash-low | notes | P | - | Y | Y | Y | Y | n | Y | Y | - | Y | Y | Y | 3322 | 99 |
| agy-oss | none | f | - | Y | n | n | Y | n | Y | Y | - | n | Y | Y | 1961 | 31 |
| agy-oss | follow | P | - | Y | n | Y | Y | n | Y | Y | - | n | n | n | 1538 | 53 |
| agy-oss | example | P | - | Y | n | Y | Y | n | Y | Y | - | n | Y | Y | 1947 | 48 |
| agy-oss | notes | P | - | Y | n | Y | Y | n | Y | Y | - | n | n | n | 1585 | 24 |

