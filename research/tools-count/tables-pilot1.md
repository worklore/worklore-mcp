# Tables (pilot)

Status counts per model (ok = scored; error/timeout = counted as failures in accuracy; ratelimited = missing, excluded):

| model | ok | error | timeout | ratelimited (missing) |
|---|---|---|---|---|
| claude | 60 | 0 | 0 | 0 |

## Claude Opus 5.5 (Claude Code)

| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 15 | 100% | 80%–100% | 100% | 100% | 0% | 0% | 1.27 | 4077 | 9509 | 175 | 6.3 | 0.0387 |
| 25 | 15 | 100% | 80%–100% | 100% | 100% | 0% | 0% | 1.40 | 7407 | 17583 | 184 | 7.0 | 0.0537 |
| 50 | 15 | 100% | 80%–100% | 100% | 100% | 0% | 0% | 1.33 | 11676 | 27519 | 182 | 6.4 | 0.0342 |
| GROUPED | 15 | 100% | 80%–100% | 100% | 100% | 0% | 0% | 1.60 | 5478 | 14439 | 253 | 7.1 | 0.0306 |

- Linear fit, first-call input tokens = 3215 + 168.9 × N  (R² = 1.000)
- Linear fit, input tokens per run = 7534 + 400.1 × N  (R² = 1.000)

## Every failed run

| model | tools | task | kind | rep | status | called (canonical ops) | why |
|---|---|---|---|---|---|---|---|

## Success by task (share of runs, all variants pooled)

| task | kind | claude |
|---|---|---|
| t01 | simple | 4/4 |
| t02 | simple | 4/4 |
| t03 | simple | 4/4 |
| t04 | simple | 4/4 |
| t05 | simple | 4/4 |
| t06 | ambiguous | 4/4 |
| t07 | ambiguous | 4/4 |
| t08 | ambiguous | 4/4 |
| t09 | ambiguous | 4/4 |
| t10 | ambiguous | 4/4 |
| t11 | ambiguous | 4/4 |
| t12 | ambiguous | 4/4 |
| t13 | chain | 4/4 |
| t14 | chain | 4/4 |
| t15 | chain | 4/4 |

