# Why the second publish returned 500

## Cause

`publish()` stores each story together with its three most similar existing
stories, computed by `similarity()` in `src/app.py`. That function blended
tag/word Jaccard ratios with `round(0.7 * tag_score + 0.3 * word_score, 4)`,
which is a Python **float**.

DynamoDB (via boto3's `TypeSerializer`) does not support floats in items — it
only accepts `Decimal` for numbers — so `table.put_item()` raised

```
TypeError: Float types are not supported. Use Decimal types instead.
```

which `handler()` catches as a generic exception and turns into a 500.

The first publish after a deploy succeeds only by accident: the table is
empty, `related()` finds no candidates, and the `similar` list is empty — so
no float ever reaches DynamoDB. Every subsequent publish has at least one
existing story, produces float `score` values in `similar`, and fails. This
matches the log exactly: `slug=why-my-cron-ran-twice similar=0 stored` (201),
then every later `POST /stories -> 500`.

The existing unit test only ever published one story, so it never exercised
the code path that writes scores.

## Fix

`src/app.py` — `similarity()` now computes in `Decimal` end to end (count
ratios as `Decimal(n) / m`, blend with `Decimal("0.7")` / `Decimal("0.3")`)
and returns the result quantized to 4 places, preserving the previous
`round(..., 4)` semantics. `Decimal` is a first-class DynamoDB number type,
so `put_item` accepts the stored `similar` scores. No floats can reach the
table from this path anymore.

`tests/test_publish.py` — added `test_second_publish_with_related_story_succeeds`,
which publishes two related stories through `handler()` and asserts both
return 201 and that the stored `similar` scores are `Decimal`. It fails with
the production `TypeError` before the fix and passes after, so the regression
can't come back.

## Verification

- `python3 -m unittest discover tests` — 2 tests, OK.
- Manual smoke test: multiple publishes through `handler()` (including
  re-publish of the same slug and stories with empty tags/bodies) all store
  items whose `similar` scores are `Decimal`.
