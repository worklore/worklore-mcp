### Sonnet 4.6: story 1 (skill-xray; Verify = the real scanner gives T4 / T0)

| arm | harness | rep | tiers (fetch / tone) | scanner fetched | pinned + hash checked | scanner run | PASS | time | tool calls |
|---|---|---|---|---|---|---|---|---|---|
| without | agy | 1 | own scale | n | - | n | fail | 35s | 5 |
| without | agy | 2 | own scale | n | - | n | fail | 32s | 5 |
| without | cc | 1 | own scale | n | - | n | fail | 40s | 8 |
| without | cc | 2 | own scale | n | - | n | fail | 24s | 5 |
| with | agy | 1 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 53s | 8 |
| with | agy | 2 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 50s | 9 |
| with | cc | 1 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 34s | 9 |
| with | cc | 2 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 29s | 5 |

### Sonnet 4.6: story 3 (author-local dates)

| arm | harness | rep | a own date | b order | c third-zone reader | d no-date caller | PASS new Verify | PASS old Verify | time | tool calls |
|---|---|---|---|---|---|---|---|---|---|---|
| without | agy | 1 | Y | Y | Y | Y | **PASS** | **PASS** | 50s | 5 |
| without | agy | 2 | Y | n | Y | Y | fail | fail | 48s | 5 |
| without | cc | 1 | Y | n | Y | Y | fail | fail | 94s | 8 |
| without | cc | 2 | Y | n | Y | Y | fail | fail | 116s | 11 |
| with | agy | 1 | Y | Y | Y | Y | **PASS** | **PASS** | 71s | 7 |
| with | agy | 2 | Y | Y | Y | Y | **PASS** | **PASS** | 77s | 7 |
| with | cc | 1 | Y | Y | Y | Y | **PASS** | **PASS** | 98s | 7 |
| with | cc | 2 | Y | Y | Y | Y | **PASS** | **PASS** | 83s | 7 |

### Opus 4.6: story 1 (skill-xray; Verify = the real scanner gives T4 / T0)

| arm | harness | rep | tiers (fetch / tone) | scanner fetched | pinned + hash checked | scanner run | PASS | time | tool calls |
|---|---|---|---|---|---|---|---|---|---|
| without | agy | 1 | own scale | n | - | n | fail | 82s | 14 |
| without | cc | 1 | own scale | n | - | n | fail | 32s | 5 |
| with | agy | 1 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 50s | 9 |
| with | cc | 1 | T4 / T0 | Y | pinned + hash | Y | **PASS** | 44s | 10 |

### Opus 4.6: story 3 (author-local dates)

| arm | harness | rep | a own date | b order | c third-zone reader | d no-date caller | PASS new Verify | PASS old Verify | time | tool calls |
|---|---|---|---|---|---|---|---|---|---|---|
| without | agy | 1 | Y | Y | Y | Y | **PASS** | **PASS** | 99s | 10 |
| without | cc | 1 | Y | n | Y | Y | fail | fail | 98s | 9 |
| with | agy | 1 | Y | Y | Y | Y | **PASS** | **PASS** | 76s | 7 |
| with | cc | 1 | Y | Y | Y | Y | **PASS** | **PASS** | 78s | 9 |

