# Why the second publish returned 500

## Cause

`similarity()` in `src/app.py` returned a Python `float` (e.g. `0.85`), and that
float ended up in the item's `similar: [{slug, score}]` list.

DynamoDB has no float type: boto3's serializer only accepts `Decimal` for
numbers and raises `TypeError: Float types are not supported. Use Decimal
types instead.` (exactly the traceback in `logs/error.log`).

Why it only broke on the *second* publish: `similar` is computed from the
stories already in the table. The first publish landed in an empty table, so
`related()` returned `[]` — no float ever reached `put_item`, and it succeeded.
From the second publish on, there was at least one existing story, so the item
contained a float `score` and `put_item` blew up on every publish, surfacing
as a 500 from `handler()`.

## Fix

In `src/app.py`, `similarity()` now computes the score with `Decimal`
arithmetic end-to-end (ratios as `Decimal` division, weights `Decimal("0.7")` /
`Decimal("0.3")`, still rounded to 4 places). `Decimal` is a native DynamoDB
number type, so the stored item is valid on every publish, not just the first.
This covers all paths that put a score into the item — there's no special-case
for "second publish".

A regression test (`test_second_publish_stores_similar_scores` in
`tests/test_publish.py`) publishes twice against the boto3-validating fake
table, so a float score can never come back.

Verified: `python3 -m unittest discover tests` passes (2 tests), and the
handler returns 201 for both the first and second `POST /stories`.
