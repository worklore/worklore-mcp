# Why the second publish returns 500

**Cause:** `related()` in `src/app.py` put `similarity()` results (Python `float`, via `round(...)`) into
`item["similar"][*]["score"]`. boto3's DynamoDB serializer rejects floats
(`TypeError: Float types are not supported. Use Decimal types instead.`).
The first publish worked only because the table was empty, so `similar` was `[]` and no float was written.
Every publish after that has at least one related story and so fails; the handler's catch-all turns it into a 500.

**Fix:** scores are stored as `Decimal(str(score))` in `related()`, so no float ever reaches `put_item`.

**Prevention:** `tests/test_publish.py` now has a test that publishes several stories in a row (the case that
was never covered). The fake table already rejects floats like boto3 does, so this test fails if a float returns.
