# Tables (full)

Status counts per model (ok = scored; error/timeout = counted as failures in accuracy; ratelimited = missing, excluded):

| model | ok | error | timeout | ratelimited (missing) |
|---|---|---|---|---|
| claude | 468 | 0 | 0 | 0 |
| claude-search | 252 | 0 | 0 | 0 |
| codex | 468 | 0 | 0 | 0 |
| gemini | 468 | 0 | 0 | 0 |

## Claude Opus 5.5 (Claude Code, tool search off)

| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | failed calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 4082 | 9336 | 189 | 6.0 | 0.0258 |
| 10 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.28 | 0.00 | 4832 | 11287 | 193 | 6.3 | 0.0354 |
| 15 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.28 | 0.00 | 5734 | 13315 | 182 | 6.4 | 0.0381 |
| 20 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.31 | 0.00 | 6597 | 15302 | 190 | 6.3 | 0.0400 |
| 25 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.36 | 0.00 | 7415 | 17823 | 194 | 6.6 | 0.0278 |
| 30 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.00 | 8225 | 19491 | 191 | 6.7 | 0.0395 |
| 35 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.42 | 0.00 | 9012 | 22127 | 201 | 6.4 | 0.0390 |
| 40 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.47 | 0.00 | 9961 | 24419 | 203 | 6.5 | 0.0344 |
| 45 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.47 | 0.00 | 10853 | 26908 | 217 | 6.6 | 0.0340 |
| 50 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.39 | 0.00 | 11679 | 27897 | 198 | 6.2 | 0.0299 |
| 75 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.00 | 15800 | 37157 | 188 | 6.1 | 0.0344 |
| 100 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.39 | 0.00 | 20222 | 48619 | 188 | 6.7 | 0.0377 |
| GROUPED | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.61 | 0.00 | 5494 | 14176 | 246 | 6.8 | 0.0287 |

- Linear fit on N = 5–50, first-call input tokens = 3182 + 169.3 × N  (R² = 1.000); at N=75: predicted 15882, measured 15800 (-0.5%); at N=100: predicted 20116, measured 20222 (+0.5%)
- Linear fit on N = 5–50, input tokens per run = 6989 + 429.2 × N  (R² = 0.997); at N=75: predicted 39176, measured 37157 (-5.2%); at N=100: predicted 49905, measured 48619 (-2.6%)

## Claude Opus 5.5 (Claude Code, tool search on = default)

| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | failed calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 3929 | 13839 | 321 | 8.5 | 0.0339 |
| 10 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.28 | 0.00 | 4001 | 14334 | 317 | 9.5 | 0.0346 |
| 25 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.44 | 0.00 | 4238 | 15622 | 317 | 7.9 | 0.0370 |
| 50 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.53 | 0.00 | 4612 | 17421 | 338 | 11.0 | 0.0412 |
| 75 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.58 | 0.00 | 5007 | 19060 | 337 | 7.9 | 0.0445 |
| 100 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.50 | 0.00 | 5396 | 19911 | 331 | 9.4 | 0.0474 |
| GROUPED | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.47 | 0.00 | 3940 | 16057 | 350 | 9.1 | 0.0387 |

- Linear fit on N = 5–50, first-call input tokens = 3852 + 15.2 × N  (R² = 1.000); at N=75: predicted 4994, measured 5007 (+0.3%); at N=100: predicted 5375, measured 5396 (+0.4%)
- Linear fit on N = 5–50, input tokens per run = 13527 + 79.0 × N  (R² = 0.997); at N=75: predicted 19451, measured 19060 (-2.0%); at N=100: predicted 21425, measured 19911 (-7.1%)

## GPT-6.1-sol (Codex CLI default)

| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | failed calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 13203 | 45323 | 133 | 13.0 |  |
| 10 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 13203 | 46828 | 134 | 13.8 |  |
| 15 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 13203 | 47826 | 132 | 13.5 |  |
| 20 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.28 | 0.00 | 13202 | 50307 | 135 | 14.8 |  |
| 25 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.00 | 13203 | 52276 | 136 | 14.0 |  |
| 30 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.42 | 0.00 | 13203 | 55347 | 143 | 13.2 |  |
| 35 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.56 | 0.00 | 13202 | 56292 | 141 | 15.2 |  |
| 40 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.56 | 0.00 | 13202 | 57949 | 143 | 14.3 |  |
| 45 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.69 | 0.00 | 13203 | 63983 | 149 | 14.9 |  |
| 50 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.56 | 0.00 | 13203 | 61417 | 142 | 14.2 |  |
| 75 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.58 | 0.00 | 13203 | 68798 | 144 | 13.3 |  |
| 100 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.72 | 0.00 | 13202 | 78240 | 151 | 13.8 |  |
| GROUPED | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.50 | 0.00 | 13202 | 50611 | 146 | 14.9 |  |

- Linear fit on N = 5–50, first-call input tokens = 13203 + -0.0 × N  (R² = 0.131); at N=75: predicted 13202, measured 13203 (+0.0%); at N=100: predicted 13202, measured 13202 (+0.0%)
- Linear fit on N = 5–50, input tokens per run = 42536 + 408.0 × N  (R² = 0.958); at N=75: predicted 73133, measured 68798 (-5.9%); at N=100: predicted 83332, measured 78240 (-6.1%)

## Gemini 3.1 Pro (Antigravity)

| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | failed calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.39 | 0.14 | 3833 | 15680 | 841 | 19.5 |  |
| 10 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.25 | 0.03 | 3856 | 15192 | 836 | 19.1 |  |
| 15 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 3880 | 14945 | 776 | 18.3 |  |
| 20 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.28 | 0.06 | 3906 | 15393 | 781 | 18.6 |  |
| 25 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 3932 | 15115 | 789 | 18.8 |  |
| 30 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.31 | 0.08 | 3954 | 15715 | 873 | 19.6 |  |
| 35 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.08 | 3978 | 16445 | 861 | 20.0 |  |
| 40 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.31 | 0.08 | 4003 | 15779 | 875 | 19.6 |  |
| 45 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.47 | 0.25 | 4026 | 16529 | 877 | 20.7 |  |
| 50 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.81 | 0.53 | 4054 | 20500 | 1057 | 23.0 |  |
| 75 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.47 | 0.25 | 4185 | 17385 | 915 | 19.9 |  |
| 100 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.97 | 0.61 | 4309 | 18577 | 808 | 19.9 |  |
| GROUPED | 36 | 89% | 75%–96% | 94% | 94% | 8% | 15% | 3.47 | 1.50 | 3832 | 34071 | 1558 | 31.3 |  |

- Linear fit on N = 5–50, first-call input tokens = 3807 + 4.9 × N  (R² = 1.000); at N=75: predicted 4175, measured 4185 (+0.2%); at N=100: predicted 4298, measured 4309 (+0.3%)
- Linear fit on N = 5–50, input tokens per run = 14107 + 73.5 × N  (R² = 0.470); at N=75: predicted 19622, measured 17385 (-11.4%); at N=100: predicted 21460, measured 18577 (-13.4%)

## Tool search (claude-search lane)

ToolSearch calls per run; `select:` = loaded by exact name from the deferred-name list, keyword = a free-text search. Off-target = a search returned tools but none the task needed. Not found = a needed tool never came back from any search. Hid = not found AND the run then went wrong (wrong tool executed or expected call missing).

| tools | ok runs | model calls/run | ToolSearch calls/run | keyword searches/run | tools loaded/run | runs with an off-target search | runs where a needed tool was never found | runs where search hid the right tool |
|---|---|---|---|---|---|---|---|---|
| 5 | 36 | 3.22 | 1.00 | 0.00 | 1.22 | 0 | 0 | 0 |
| 10 | 36 | 3.28 | 1.00 | 0.00 | 1.28 | 0 | 0 | 0 |
| 25 | 36 | 3.36 | 1.00 | 0.00 | 1.53 | 0 | 0 | 0 |
| 50 | 36 | 3.44 | 1.00 | 0.00 | 1.72 | 0 | 0 | 0 |
| 75 | 36 | 3.50 | 1.00 | 0.00 | 1.64 | 0 | 0 | 0 |
| 100 | 36 | 3.42 | 1.00 | 0.00 | 1.58 | 0 | 0 | 0 |
| GROUPED | 36 | 3.47 | 1.00 | 0.00 | 1.69 | 0 | 0 | 0 |

## Every failed run

| model | tools | task | kind | rep | status | called (canonical ops) | why |
|---|---|---|---|---|---|---|---|
| gemini | GROUPED | t08 | ambiguous | 1 | ok | pdf_None|pdf_help|pdf_merge|pdf_images_to_pdf | expected tool(s) missing/out of order; wrong tool: pdf_merge |
| gemini | GROUPED | t08 | ambiguous | 2 | ok | doc_convert?|pdf_None|pdf_from_images|pdf_merge|pdf_from_images|pdf_merge|pdf_info|pdf_info | wrong tool: pdf_merge |
| gemini | GROUPED | t10 | ambiguous | 1 | ok | pdf_extract_text|pdf_extract_text|pdf_extract_text|pdf_extract_text|pdf_extract_text | expected tool(s) missing/out of order |
| gemini | GROUPED | t17 | ambiguous | 1 | ok | pdf_None|pdf_remove|pdf_help|pdf_delete|pdf_remove_pages|pdf_info|pdf_info|pdf_delete|pdf_split|pdf_extract|pdf_rotate|pdf_delete_pages|pdf_delete_pages|pdf_delete_pages|pdf_info | wrong tool: pdf_split |

## Success by task (share of runs, all variants pooled)

| task | kind | claude | claude-search | codex | gemini |
|---|---|---|---|---|---|
| t01 | simple | 26/26 | 14/14 | 26/26 | 26/26 |
| t02 | simple | 26/26 | 14/14 | 26/26 | 26/26 |
| t03 | simple | 26/26 | 14/14 | 26/26 | 26/26 |
| t04 | simple | 26/26 | 14/14 | 26/26 | 26/26 |
| t05 | simple | 26/26 | 14/14 | 26/26 | 26/26 |
| t06 | ambiguous | 26/26 | 14/14 | 26/26 | 26/26 |
| t07 | ambiguous | 26/26 | 14/14 | 26/26 | 26/26 |
| t08 | ambiguous | 26/26 | 14/14 | 26/26 | 24/26 |
| t09 | ambiguous | 26/26 | 14/14 | 26/26 | 26/26 |
| t10 | ambiguous | 26/26 | 14/14 | 26/26 | 25/26 |
| t11 | ambiguous | 26/26 | 14/14 | 26/26 | 26/26 |
| t12 | ambiguous | 26/26 | 14/14 | 26/26 | 26/26 |
| t13 | chain | 26/26 | 14/14 | 26/26 | 26/26 |
| t14 | chain | 26/26 | 14/14 | 26/26 | 26/26 |
| t15 | chain | 26/26 | 14/14 | 26/26 | 26/26 |
| t16 | ambiguous | 26/26 | 14/14 | 26/26 | 26/26 |
| t17 | ambiguous | 26/26 | 14/14 | 26/26 | 25/26 |
| t18 | ambiguous | 26/26 | 14/14 | 26/26 | 26/26 |

