# Second publish failure

`logs/error.log` shows the second `POST /stories` failing inside `table.put_item` with `TypeError: Float types are not supported. Use Decimal types instead.` The first publish scans an empty table, so `related()` returns no matches. Once a story exists, `similarity()` produces a Python float and `related()` places it in the nested `similar[].score` field. Boto3 rejects that float while serializing the item, and `handler()` returns 500.

`similarity()` now converts its rounded score to `Decimal` before the score can enter an item. This keeps the existing four-decimal score scale while giving DynamoDB a supported numeric type. A regression test publishes two stories through `handler()` against the validating in-memory table, checks that both requests return 201, and checks that the second item stores a `Decimal` score. `python3 -m unittest discover tests` passes (2 tests).

The colleague's note applies to the state-dependent path, the DynamoDB float restriction, and the need for a test with an existing record. Its integer-percentage conversion was not used because it would discard the current score precision; `Decimal` preserves it. Its suggested real-table verification was not performed because this task is limited to the current directory and forbids external publishing.
