# Second publish failure

The first publish finds no existing stories, so `similar` is empty. On the second publish, `similarity()` calculates a score with Python float division and float weights. `related()` places that float in `similar[].score`, and boto3 rejects it during `put_item`, causing the logged 500: `Float types are not supported. Use Decimal types instead.`

`similarity()` now uses `Decimal` for both ratios and weights and quantizes the result to four decimal places. Scores retain their 0–1 meaning and can be serialized by DynamoDB. A regression test publishes two stories through the handler using the DynamoDB-validating fake table, then checks the stored related score. `python3 -m unittest discover tests -v` passes (2 tests).

The colleague's note applied to the empty-table versus populated-table path, the boto3 float restriction, and the need for a seeded second-write test. Its proposed integer-percentage fix was not used because it would change the score scale and precision. Publishing twice against a real table was not done because the task requires all work to stay local and forbids external publishing.
