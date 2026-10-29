# Second publish returns 500: `TypeError: Float types are not supported`

## Cause

`similarity()` in `src/app.py` returns a Python float (`round(..., 4)`). `related()`
puts that float into each entry of `similar` (`[{slug, score}]`), and `publish()`
writes the item with `table.put_item`. boto3 refuses floats, so the write raises.

The first publish worked because the table was empty: `related()` had nothing to
score, so `similar` was `[]` and no float was ever written. The second publish is
the first one that has a related story to score. The existing tests only ever
published into an empty `FakeTable`, so they never reached this path.

Reproduced locally: publish one story, then a second one with overlapping tags.
Before the fix the second publish raises the same `TypeError` as
`logs/error.log` (09:21:47 and 09:22:10).

## Fix

`src/app.py`, in `publish()`: each score is converted to `decimal.Decimal` when the
item is built, using its 4-decimal string form, so the stored value is the same
number as before:

```python
similar = [
    {"slug": s["slug"], "score": Decimal(str(s["score"]))}
    for s in related(story, existing)
]
```

`similarity()` and `related()` still return floats, so the scoring logic is
unchanged. The HTTP response only returns `slug`, so the API contract doesn't change.

## Making it stay fixed

- `tests/test_publish.py` gains two tests that exercise the populated path:
  - `test_second_publish_with_related_stories_is_stored` seeds one story, writes a
    second that has a related story, and checks the stored `similar` entry.
  - `test_handler_second_publish_returns_201` runs two publishes through `handler()`
    and expects 201 for both, which matches the production symptom.
- Against the original `app.py`, both new tests fail (one ERROR, one FAIL). With the
  fix, all three tests pass (`python3 -m unittest discover tests`).
- `tests/fake_dynamo.py` already rejects floats the way boto3 does, so any new float in
  an item will now fail the test suite instead of production.

## Colleague's note: what applied

- **Applied:** the diagnosis. Only the state-dependent path (similarity scores) produces
  a float, and the empty-table first write hides it.
- **Applied:** trace every value that feeds a write. I grepped for `round(`, `/`,
  `float(`, `sum(` and `mean`. The only float that reaches an item is the score; the
  divisions in `similarity()` feed only that score. `published_at` is already an `int`.
- **Applied:** convert at the boundary. I used `Decimal`, not the integer-percentage
  change the note describes, because the score is a 0–1 value that other code may read.
  Changing it to a percentage would change the stored data.
- **Applied:** seed a record, then write a second one in tests. This is the two new tests.
- **Not applied:** "publish twice against a real table." I have no AWS access here, and
  the ground rules forbid publishing to an external service, so this still needs doing
  by you after a deploy. The seeded test covers the same code path with the in-memory table.

## Not changed (noticed while tracing)

- `publish()` calls `table.scan(TableName=...)` once and does not follow
  `LastEvaluatedKey`. DynamoDB returns at most 1 MB per scan, so once the table grows
  past that, `similar` is computed from a partial library. This is a correctness issue
  but not the 500, so I left it alone.
