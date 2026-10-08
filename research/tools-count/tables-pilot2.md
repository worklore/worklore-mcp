# Tables (pilot2)

Status counts per model (ok = scored; error/timeout = counted as failures in accuracy; ratelimited = missing, excluded):

| model | ok | error | timeout | ratelimited (missing) |
|---|---|---|---|---|
| claude | 72 | 0 | 0 | 0 |

## Claude Opus 5.5 (Claude Code)

| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | failed calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 18 | 100% | 82%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 4082 | 9335 | 186 | 6.4 | 0.0309 |
| 25 | 18 | 100% | 82%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.00 | 7415 | 17599 | 182 | 6.7 | 0.0362 |
| 50 | 18 | 100% | 82%–100% | 100% | 100% | 0% | 0% | 1.44 | 0.00 | 11679 | 28912 | 204 | 7.3 | 0.0303 |
| GROUPED | 18 | 100% | 82%–100% | 100% | 100% | 0% | 0% | 1.50 | 0.00 | 5480 | 14109 | 235 | 7.3 | 0.0282 |

- Linear fit on N = 5–50, first-call input tokens = 3222 + 168.9 × N  (R² = 1.000)
- Linear fit on N = 5–50, input tokens per run = 6995 + 435.8 × N  (R² = 0.999)

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
| t16 | ambiguous | 4/4 |
| t17 | ambiguous | 4/4 |
| t18 | ambiguous | 4/4 |

