# Why the second publish failed

`logs/error.log` shows `TypeError: Float types are not supported. Use Decimal types instead` during `table.put_item`. The first publish scans an empty table, so its `similar` list is empty and the item contains no score. On the next publish, `related()` adds a score from `similarity()`, which returns a Python `float`. Boto3 rejects that nested float while serializing the item for DynamoDB, and the handler returns 500.

# Fix and prevention

`related()` now converts each computed score to `Decimal` before it enters the item sent to DynamoDB. The conversion uses `Decimal(str(score))` to preserve the existing rounded score without importing binary floating point artifacts into the stored value.

The regression test publishes into a populated fake table through the handler and checks both fractional and zero related scores. The fake validates DynamoDB value types, so a future float in this path fails the test. Run it with `python3 -m unittest discover tests -v` (2 tests pass). No external table was used.

# Colleague's note

The note's diagnosis applies: a computed related score introduces a float only when an earlier story exists, and DynamoDB rejects it. Its advice to test a seeded write path also applies. I used `Decimal` rather than integer percentages to retain the existing four decimal place scoring contract. Its suggestion to publish twice against a real table was not applicable here because this task is restricted to local work and the fake table already checks the relevant serialization rule.
