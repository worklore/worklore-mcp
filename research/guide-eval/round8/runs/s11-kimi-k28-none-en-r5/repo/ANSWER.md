# Why the second publish returned 500

## Cause

`similarity()` in `src/app.py` computes its score with float arithmetic
(`/` division, `0.7 * ... + 0.3 * ...`, `round(..., 4)`), so every score it
returns is a Python `float`. boto3's DynamoDB serializer rejects floats
(`TypeError: Float types are not supported. Use Decimal types instead.`) —
DynamoDB numbers must be `Decimal`.

The `float` only reaches DynamoDB inside the `similar` list, so whether a
publish fails depends on how many stories are already in the table:

- **First publish:** the table is empty, `related()` returns `[]`, the item
  contains only strings/ints, and `put_item` succeeds (201). This matches the
  log line `similar=0 stored`.
- **Second publish:** the table now has one story, so `similar` contains
  `{"slug": ..., "score": <float>}` and `put_item` raises the `TypeError`.
  The handler's catch-all turns it into a 500 — and every publish after that
  fails the same way, exactly as `logs/error.log` shows.

The bug shipped because the test suite only ever exercised a single publish;
nothing put a float into an item until production traffic did.

## Fix

- `src/app.py` — `similarity()` now returns `Decimal(str(round(score, 4)))`
  instead of a float, so the scores stored in `similar` are DynamoDB-safe.
  (`str()` round-trips through the rounded decimal string, avoiding binary
  float artifacts.) This fixes the root cause for every publish, not just one.
- `tests/test_publish.py` — added `test_second_publish_does_not_500`, which
  publishes two stories through `handler()` and asserts the second returns
  201 and that stored `similar` scores are `Decimal`. It fails against the
  old code with the same `TypeError` from production, so the regression
  can't come back unnoticed.

Verified with `python3 -m unittest discover tests` (2 tests, OK).
