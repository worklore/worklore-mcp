# Why the second publish returns 500

**Cause:** `related()` in `src/app.py` puts a similarity `score` into the item's `similar` list, and `similarity()` returns a Python `float` (a `round(...)` of a blend of ratios). boto3's DynamoDB serializer rejects floats, so `put_item` raises `TypeError: Float types are not supported. Use Decimal types instead.` (see `logs/error.log`). The first publish worked only because the table was empty. There were no other stories to score, so `similar` was `[]` and no float existed. From the second publish on, `similar` holds scores and every write fails. The tests only covered the empty-table path, so nothing caught it.

**Fix:**
- `src/app.py`: `related()` now stores `Decimal(str(similarity(...)))`. Going through `str` keeps the rounded value exact, with no binary-float noise.
- `tests/test_publish.py`: new test that publishes two and then three stories against a populated table. The fake table rejects floats the way boto3 does, so this fails if a float comes back.

**Why it can't come back:** the test now covers the populated-table path, and `FakeTable` raises on any float, so reintroducing one fails the test.
