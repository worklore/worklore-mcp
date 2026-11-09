# Why the second publish returned 500

## Cause

`similarity()` in `src/app.py` returned a Python `float`
(`round(0.7 * tag_score + 0.3 * word_score, 4)`), and that float was stored
in each new item's `similar: [{slug, score}]` list. DynamoDB's wire format
has no float type — boto3's serializer only accepts `Decimal` for numbers —
so `table.put_item()` raised `TypeError: Float types are not supported. Use
Decimal types instead.` (`logs/error.log` lines 3–25).

The bug was invisible on the first publish: with an empty table, `related()`
returns `[]`, so no float ever reached `put_item` and the item stored fine.
Starting with the second publish there is at least one existing story, so
`similar` contained a float `score` and every publish after the first failed
with 500. The exception happened inside the broad `except Exception` in
`handler()`, which is why the client saw a bare 500.

## Fix

`src/app.py:similarity()` now computes the score with `Decimal` arithmetic
(`Decimal(count) / Decimal(count)` for the Jaccard ratios, weights as
`Decimal("0.7")` / `Decimal("0.3")`, and `round(..., 4)` on the Decimal
result), so the value is DynamoDB-safe by construction instead of being
converted at the boundary.

## So it can't come back

`tests/test_publish.py` gains `test_second_publish_stores_similar_as_dynamodb_safe_numbers`:
it publishes two overlapping stories through `handler()`, asserts both return
201, and asserts the stored `similar` scores are `Decimal`. The in-memory
`FakeTable` validates every item exactly like boto3's TypeSerializer (it
rejects floats), so any future float reaching `put_item` — from this path or
a new one — fails the test with the same `TypeError` production would raise.

Verified with `python3 -m unittest discover tests` (2 tests, OK) and by
replaying the logged scenario: three consecutive publishes all return 201
with `Decimal` scores.
