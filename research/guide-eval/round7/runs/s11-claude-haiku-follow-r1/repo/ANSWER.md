# Why the second publish returns 500

## Cause

`publish()` stores each story with `similar`: the top three existing stories and
their scores. The score comes from `similarity()` in `src/app.py`, which returns
`round(..., 4)`, a Python `float`. `related()` put that float straight into the
item.

On the first publish the table is empty, so `existing` is empty, `related()`
returns `[]`, and no float is written. The second publish finds one story, builds
`similar: [{"slug": ..., "score": 0.425}]`, and boto3 rejects the float:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The existing test only published into an empty `FakeTable`, so it never reached
the scoring code. It passed while the bug was in the code.

## Fix

`related()` now stores the score as a `Decimal`:

```python
scored.append({"slug": other["slug"], "score": Decimal(str(similarity(story, other)))})
```

`Decimal(str(x))` keeps the 4-digit value exactly (`0.425` stays `Decimal('0.425')`).
The reader sees the same numbers as before. I did not switch to integer
percentages, because that would change what the stored score means.

## Keeping it fixed

- `tests/test_publish.py` has two new tests that exercise the populated path:
  - `test_publish_with_existing_stories_stores_scores` seeds one story, publishes
    a second, and checks that the score is stored as a related entry.
  - `test_handler_second_publish_returns_201` runs two publishes through
    `handler()`, the path that returned 500 in production.
- `tests/fake_dynamo.py` already rejects `float` values the way boto3 does, so any
  future computed float written to an item fails the tests instead of production.

## Verification

- `python3 -m unittest discover tests` (run from the repo root): 3 tests, OK.
- Before the fix, the two new tests failed with the same `TypeError` and a `500`.
- The only `/` and `round(` in the write path are in `similarity()`, and their
  result now goes through `Decimal`.

Not done: publishing twice against a real DynamoDB table. The ground rules rule
out publishing to external services, so this was verified against the in-memory
table only.
