# Tables (cheap)

Status counts per model (ok = scored; error/timeout = counted as failures in accuracy; ratelimited = missing, excluded):

| model | ok | error | timeout | ratelimited (missing) |
|---|---|---|---|---|
| claude | 468 | 0 | 0 | 0 |
| codex | 468 | 0 | 0 | 0 |
| gemini | 464 | 4 | 0 | 0 |

## Claude Haiku 5.5 (Claude Code, tool search off)

| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | failed calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 4994 | 11357 | 187 | 4.5 | 0.0010 |
| 10 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.31 | 0.00 | 5743 | 13556 | 216 | 4.9 | 0.0011 |
| 15 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.31 | 0.00 | 6645 | 15621 | 213 | 4.8 | 0.0012 |
| 20 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.00 | 7509 | 17799 | 188 | 4.6 | 0.0013 |
| 25 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.44 | 0.00 | 8326 | 20686 | 201 | 4.7 | 0.0013 |
| 30 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.56 | 0.00 | 9136 | 22473 | 226 | 5.2 | 0.0013 |
| 35 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.58 | 0.00 | 9923 | 25778 | 240 | 5.2 | 0.0013 |
| 40 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.61 | 0.00 | 10872 | 27893 | 236 | 4.9 | 0.0012 |
| 45 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.78 | 0.00 | 11763 | 31246 | 267 | 5.4 | 0.0012 |
| 50 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.72 | 0.00 | 12590 | 32643 | 259 | 5.0 | 0.0012 |
| 75 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.69 | 0.00 | 16711 | 44117 | 239 | 5.2 | 0.0013 |
| 100 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.61 | 0.00 | 21133 | 53818 | 233 | 5.2 | 0.0013 |
| GROUPED | 36 | 94% | 82%–98% | 100% | 94% | 0% | 0% | 1.94 | 0.00 | 6405 | 18051 | 304 | 5.4 | 0.0011 |

- Linear fit on N = 5–50, first-call input tokens = 4094 + 169.3 × N  (R² = 1.000); at N=75: predicted 16793, measured 16711 (-0.5%); at N=100: predicted 21026, measured 21133 (+0.5%)
- Linear fit on N = 5–50, input tokens per run = 8489 + 487.9 × N  (R² = 0.997); at N=75: predicted 45079, measured 44117 (-2.1%); at N=100: predicted 57276, measured 53818 (-6.0%)

## GPT-Reserve (Codex CLI)

| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | failed calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.28 | 0.00 | 10478 | 47941 | 360 | 11.2 |  |
| 10 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.25 | 0.00 | 10478 | 48489 | 335 | 10.6 |  |
| 15 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.22 | 0.00 | 10478 | 50145 | 340 | 10.5 |  |
| 20 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.00 | 10478 | 49993 | 361 | 10.4 |  |
| 25 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.72 | 0.00 | 10478 | 57774 | 369 | 11.6 |  |
| 30 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.94 | 0.00 | 10478 | 62996 | 389 | 11.9 |  |
| 35 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 2.25 | 0.00 | 10479 | 68910 | 407 | 12.6 |  |
| 40 | 36 | 97% | 86%–100% | 100% | 100% | 3% | 0% | 2.31 | 0.00 | 10479 | 73907 | 430 | 11.7 |  |
| 45 | 36 | 97% | 86%–100% | 100% | 100% | 3% | 5% | 2.14 | 0.00 | 10479 | 70741 | 383 | 11.5 |  |
| 50 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.97 | 0.00 | 10479 | 70587 | 407 | 12.1 |  |
| 75 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 2.47 | 0.00 | 10478 | 93515 | 452 | 13.5 |  |
| 100 | 36 | 94% | 82%–98% | 100% | 100% | 6% | 5% | 2.61 | 0.00 | 10479 | 103846 | 471 | 13.8 |  |
| GROUPED | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 2.22 | 0.00 | 10478 | 61774 | 404 | 12.5 |  |

- Linear fit on N = 5–50, first-call input tokens = 10478 + 0.0 × N  (R² = 0.633); at N=75: predicted 10479, measured 10478 (-0.0%); at N=100: predicted 10479, measured 10479 (-0.0%)
- Linear fit on N = 5–50, input tokens per run = 42136 + 655.0 × N  (R² = 0.895); at N=75: predicted 91260, measured 93515 (+2.5%); at N=100: predicted 107635, measured 103846 (-3.5%)

## Gemini 3.8 Flash low (Antigravity)

| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | failed calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.03 | 3562 | 14716 | 313 | 12.5 |  |
| 10 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.31 | 0.00 | 3585 | 14818 | 381 | 12.9 |  |
| 15 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.00 | 3610 | 15143 | 374 | 12.8 |  |
| 20 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.25 | 0.00 | 3636 | 14308 | 323 | 12.1 |  |
| 25 | 36 | 94% | 82%–98% | 94% | 94% | 0% | 0% | 1.24 | 0.00 | 3663 | 15018 | 334 | 12.1 |  |
| 30 | 36 | 97% | 86%–100% | 100% | 100% | 3% | 5% | 1.44 | 0.00 | 3683 | 17456 | 479 | 14.3 |  |
| 35 | 36 | 97% | 86%–100% | 97% | 97% | 0% | 0% | 1.57 | 0.00 | 3707 | 17477 | 436 | 13.8 |  |
| 40 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.47 | 0.00 | 3733 | 16864 | 458 | 13.6 |  |
| 45 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.00 | 3756 | 15605 | 340 | 12.4 |  |
| 50 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.33 | 0.00 | 3784 | 15586 | 388 | 12.5 |  |
| 75 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 1.39 | 0.06 | 3916 | 16127 | 403 | 13.9 |  |
| 100 | 36 | 100% | 90%–100% | 100% | 100% | 0% | 0% | 2.00 | 0.33 | 4040 | 23345 | 729 | 17.3 |  |
| GROUPED | 36 | 97% | 86%–100% | 100% | 100% | 3% | 5% | 2.75 | 1.17 | 3561 | 23053 | 484 | 16.8 |  |

- Linear fit on N = 5–50, first-call input tokens = 3537 + 4.9 × N  (R² = 1.000); at N=75: predicted 3905, measured 3916 (+0.3%); at N=100: predicted 4027, measured 4040 (+0.3%)
- Linear fit on N = 5–50, input tokens per run = 14570 + 41.1 × N  (R² = 0.288); at N=75: predicted 17650, measured 16127 (-8.6%); at N=100: predicted 18677, measured 23345 (+25.0%)

## Every failed run

| model | tools | task | kind | rep | status | called (canonical ops) | why |
|---|---|---|---|---|---|---|---|
| claude | GROUPED | t15 | chain | 1 | ok | image_convert|image_strip_metadata|image_resize | key args wrong |
| claude | GROUPED | t15 | chain | 2 | ok | image_convert|image_strip_metadata|image_resize | key args wrong |
| codex | 40 | t03 | simple | 1 | ok | qr_make|qr_read|qr_make|qr_read|qr_make|qr_make|qr_read|qr_read|html_to_pdf|pdf_info|html_to_pdf|pdf_info | wrong tool: html_to_pdf|html_to_pdf |
| codex | 100 | t03 | simple | 2 | ok | qr_make|qr_read|qr_make|qr_read|qr_make|qr_read|file_hash|file_hash|html_to_pdf|pdf_to_images|qr_read|qr_read|qr_read|file_hash|file_hash|image_info | wrong tool: html_to_pdf|pdf_to_images |
| codex | 45 | t17 | ambiguous | 1 | ok | pdf_delete_pages|pdf_info|pdf_extract_pages | wrong tool: pdf_extract_pages |
| codex | 100 | t18 | ambiguous | 2 | ok | pdf_info|pdf_to_images|pdf_extract_text|ocr_image|pdf_rotate|pdf_info|pdf_to_images | wrong tool: pdf_to_images|pdf_to_images |
| gemini | GROUPED | t08 | ambiguous | 2 | ok | doc_convert?|pdf_None|pdf_help|pdf_merge|pdf_merge|pdf_info|pdf_from_images|pdf_info | wrong tool: pdf_merge |
| gemini | 25 | t11 | ambiguous | 2 | error | (none) | error: status=ERROR {"short_error":"INVALID_ARGUMENT (code 400): * GenerateContentReque; expected tool(s) missing/out of order |
| gemini | 25 | t16 | ambiguous | 2 | error | (none) | error: status=ERROR; expected tool(s) missing/out of order |
| gemini | 35 | t16 | ambiguous | 2 | error | (none) | error: status=ERROR; expected tool(s) missing/out of order |
| gemini | 30 | t17 | ambiguous | 2 | ok | pdf_delete_pages|pdf_delete_pages|pdf_info|zip_list|pdf_extract_pages|pdf_info | wrong tool: pdf_extract_pages |

## Success by task (share of runs, all variants pooled)

| task | kind | claude | codex | gemini |
|---|---|---|---|---|
| t01 | simple | 26/26 | 26/26 | 26/26 |
| t02 | simple | 26/26 | 26/26 | 26/26 |
| t03 | simple | 26/26 | 24/26 | 26/26 |
| t04 | simple | 26/26 | 26/26 | 26/26 |
| t05 | simple | 26/26 | 26/26 | 26/26 |
| t06 | ambiguous | 26/26 | 26/26 | 26/26 |
| t07 | ambiguous | 26/26 | 26/26 | 26/26 |
| t08 | ambiguous | 26/26 | 26/26 | 25/26 |
| t09 | ambiguous | 26/26 | 26/26 | 26/26 |
| t10 | ambiguous | 26/26 | 26/26 | 26/26 |
| t11 | ambiguous | 26/26 | 26/26 | 25/26 |
| t12 | ambiguous | 26/26 | 26/26 | 26/26 |
| t13 | chain | 26/26 | 26/26 | 26/26 |
| t14 | chain | 26/26 | 26/26 | 26/26 |
| t15 | chain | 24/26 | 26/26 | 26/26 |
| t16 | ambiguous | 26/26 | 26/26 | 24/26 |
| t17 | ambiguous | 26/26 | 25/26 | 25/26 |
| t18 | ambiguous | 26/26 | 25/26 | 26/26 |

