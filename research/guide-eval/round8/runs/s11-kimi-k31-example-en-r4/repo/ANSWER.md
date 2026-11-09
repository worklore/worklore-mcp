# Cause

The second publish reached the populated-table code path. `publish()` scans existing stories, and `related()` calls `similarity()` for each one. The Jaccard calculations use `/`, producing Python floats, and the old `round(..., 4)` still returned a float. That float was stored as `similar[].score` and passed to DynamoDB by `table.put_item()`.

DynamoDB's boto3 serializer rejects Python floats, which is exactly the `TypeError: Float types are not supported. Use Decimal types instead.` in `logs/error.log`. The first publish succeeded because the table was empty: there were no existing stories to score, so `similar` was an empty list and no float was sent to DynamoDB.

# Fix

`src/app.py` now converts the blended similarity to an integer percentage from 0 to 100 at the boundary:

```python
return round(100 * (0.7 * tag_score + 0.3 * word_score))
```

Calling `round()` without `ndigits` returns an `int`, so the value stored in `similar[].score` is supported by DynamoDB. Relative score ordering is preserved.

`tests/test_publish.py` now includes a regression test that seeds the table with an existing story before publishing another one. It verifies the stored related-story result, requires the score's type to be `int`, and checks that both stories exist. The test failed with the original float-rejection error before the fix, so restoring a float score will fail it again.

# Colleague's note: what applied

Applied:

- The diagnosis that boto3/DynamoDB rejects Python floats.
- The explanation that an empty table hides the problem on the first write, while similarity scoring exposes it on the second.
- Tracing computed division/rounding results into the item sent to `put_item()`.
- Converting scores to integer percentages at the write boundary.
- Adding a populated-table write test instead of relying only on the first-write case.

Not applied:

- Publishing twice against a real AWS table. No external service was used; verification used the project's `FakeTable`, which deliberately reproduces boto3's type validation.

# Verification

- `python3 -m unittest discover tests`: 2 tests passed.
- Two consecutive `handler()` calls against `FakeTable` both returned HTTP 201. The second stored item contained `{'slug': 'first-story', 'score': 100}`, with the score confirmed as an `int`.
