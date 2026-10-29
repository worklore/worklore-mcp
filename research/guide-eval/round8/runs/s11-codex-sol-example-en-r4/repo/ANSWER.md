# Second publish failure

`logs/error.log` shows that the second request failed in `table.put_item` with `TypeError: Float types are not supported. Use Decimal types instead.` The first publish scanned an empty table, so `related()` returned an empty list. Once a story existed, `similarity()` produced a Python float and `related()` placed it in `item["similar"][0]["score"]`. DynamoDB rejected that nested float, and `handler()` returned 500.

The fix makes `similarity()` calculate and round with `decimal.Decimal` throughout. Related scores retain their existing 0–1 scale and four decimal places while using a type DynamoDB accepts. A regression test publishes two stories through `handler()` using the DynamoDB-validating fake table, then checks both responses, the stored related score, and its `Decimal` type. The test returned 500 before the fix and passes afterward; `python3 -m unittest discover tests` passes both tests. No external service was contacted.

The colleague's note correctly identified the state-dependent related-score path, DynamoDB's rejection of floats, and the need to test with an existing record. Its suggestion to store integer percentages was not used because it would change the score scale and discard precision. Its recommendation to publish against a real table was not used because this task is restricted to local work.
