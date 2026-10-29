# Second publish failure

`logs/error.log` shows boto3 raising `TypeError: Float types are not supported. Use Decimal types instead.` at `table.put_item`. The first publish scans an empty table, so `related()` returns an empty list. On the second publish, `related()` computes `similarity()` for the existing story. That function returns a Python float, which becomes `similar[0].score` in the item passed to DynamoDB. Boto3 rejects it and the handler returns 500.

`related()` now converts each rounded score to `Decimal` before adding it to the item. This preserves the existing 0–1 score scale and four-decimal rounding while making the stored value acceptable to DynamoDB. A regression test publishes twice through the handler against the validating fake table and checks that the second item contains a fractional `Decimal` score. `python3 -m unittest discover tests` passes.

The colleague's note applies to the empty-table versus populated-table path, boto3's rejection of floats, and the need for a seeded second-write test. Its integer-percentage fix was not used because it would change the stored score's scale and precision. A real-table publish was not run; this repository's tests use the local validating fake table, and the task forbids external publishing.
