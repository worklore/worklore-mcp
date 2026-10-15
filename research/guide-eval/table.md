### Story 1: skill-xray (Verify: the real scanner gives T4 and T0)

| agent | arm | tiers (fetch / tone) | scanner fetched | scanner run | PASS | time |
|---|---|---|---|---|---|---|
| claude | without | its own scale | n | n | fail | 24s |
| claude | with | T4 / T0 | n | n | fail | 28s |
| codex | without | its own scale | n | n | fail | 42s |
| codex | with | T4 / T0 | Y | Y | **PASS** | 77s |
| agy-pro | without | its own scale | n | n | fail | 193s |
| agy-pro | with | T4 / T0 | Y | Y | **PASS** | 27s |
| agy-flash | without | T4 / T0 | Y | n | fail | 582s |
| agy-flash | with | T4 / T0 | Y | Y | **PASS** | 72s |

### Story 2: MCP client-path tests

a = client harness (initialize, then tools/list, then tools/call, checked against the published outputSchema); b = new tests fail when the fix is reverted (tools.py restored); c = new tests pass with the fix; prod = hidden check against the untouched DynamoStore; d = the fake returns production types (Decimal)

| agent | arm | a | b | c | prod fixed | d | PASS | time |
|---|---|---|---|---|---|---|---|---|
| claude | without | partial: schema read from source | Y | Y | Y | no (tests hit DynamoStore directly) | fail | 82s |
| claude | with | Y | Y | Y | Y | yes | **PASS** | 87s |
| codex | without | n | Y | Y | Y | no (tests hit DynamoStore directly) | fail | 76s |
| codex | with | Y | Y | Y | Y | yes | **PASS** | 109s |
| agy-pro | without | n | Y | Y | Y | no (tests hit DynamoStore directly) | fail | 207s |
| agy-pro | with | Y | Y | Y | Y | yes | **PASS** | 116s |
| agy-flash | without | n | Y | Y | Y | no (tests hit DynamoStore directly) | fail | 438s |
| agy-flash | with | Y | Y | Y | Y | yes | **PASS** | 364s |

### Story 3: author-local dates

Verify: a = each author sees their own local date (23:30 in UTC+9 and in UTC-3); b = feed order matches submission order. The other columns are extra checks and do not affect PASS.

| agent | arm | a | b | 3-zone order | same date for every viewer | old call `publish(entry, client_tz)` still right | PASS | time |
|---|---|---|---|---|---|---|---|---|
| claude | without | Y | Y | Y | Y | Y | **PASS** | 52s |
| claude | with | Y | Y | Y | Y | Y | **PASS** | 51s |
| codex | without | Y | Y | Y | n | Y | **PASS** | 61s |
| codex | with | Y | Y | Y | Y | n: raised: ValueError: entry must include the autho | **PASS** | 116s |
| agy-pro | without | Y | Y | Y | n | Y | **PASS** | 148s |
| agy-pro | with | Y | Y | Y | Y | n: America/Argentina/Buenos_Aires | **PASS** | 98s |
| agy-flash | without | Y | Y | Y | n | Y | **PASS** | 281s |
| agy-flash | with | Y | Y | Y | Y | n: 2026-10-03 | **PASS** | 175s |
