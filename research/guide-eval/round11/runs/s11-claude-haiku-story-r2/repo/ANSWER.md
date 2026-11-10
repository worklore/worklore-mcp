# Second publish returns 500: float written to DynamoDB

## Cause

`similarity()` in `src/app.py` returns a Python float (`round(..., 4)`), and
`related()` stores that float as `similar[].score`. `publish()` then calls
`table.put_item(Item=item)` with it. boto3 rejects Python floats:

    TypeError: Float types are not supported. Use Decimal types instead.

Why the first publish worked: on an empty table, `scan()` returns no items, so
`related()` never calls `similarity()`. No score is computed, no float is
written. The bug only exists once the table holds at least one story, which is
why the first publish succeeded and the second returned 500.

Why the tests missed it: `tests/test_publish.py` only publishes into an empty
`FakeTable`, so the populated path never ran. `tests/fake_dynamo.py` already
rejects floats the way boto3 does; the test just never gave it a float.

Confirmed locally: with one story seeded, a second `publish()` fails with the
same `TypeError` as `logs/error.log`.

## Fix

1. `src/app.py`: added `for_dynamo()`, which recursively converts every float in
   the item to `decimal.Decimal(str(value))`. `publish()` calls it right before
   `put_item`. Converting via `str` keeps the exact digits (`0.1234` stays
   `0.1234`). Because it is recursive and sits at the write boundary, any future
   float (a new score, an average, a counter) is handled, not just the one
   that failed.
2. `tests/test_publish.py` (new tests):
   - `test_publish_into_populated_table`: seeds one story, publishes a second
     one, and checks that `similar` holds the first story with a positive score.
   - `test_handler_second_publish_returns_201`: same sequence through `handler()`,
     which is what the endpoint runs.
   - `test_for_dynamo_converts_nested_floats`: unit test for the conversion.

Verification:
- `python3 -m unittest discover tests`: 4 tests, all pass.
- The two populated-table tests and the converter test fail or error against
  the original `app.py`, so they catch this bug.
- The seeded repro script now prints `second write ok`.

Not verified: a publish against a real DynamoDB table. I have no AWS access
here, and publishing to an external service is outside this task. Please run
two publishes against the staging table before deploying.

## Colleague's note: what applied

- **Applied:** the root cause pattern (state-dependent code path that first-write
  tests never reach). The fix is the same shape: convert computed floats to
  `Decimal` at the boundary.
- **Applied:** "grep for `round(` and `/` feeding item dicts." The only hit is
  `round(...)` in `similarity()`. The `/` operations in `similarity()` feed `round`,
  so they are covered by the same fix.
- **Applied:** "add an integration test that seeds a record and writes a second
  one." This is `test_publish_into_populated_table` and the handler test.
- **Not applied:** converting scores to integer percentages. It works, but it
  changes what `score` means in the stored data and API (0–1 becomes 0–100), which
  the reader page may depend on. `Decimal` keeps the existing values.
- **Not applied:** "publish twice against a real table." Not possible here: no
  AWS access, and the ground rules rule out publishing to an external service.
- **Not applied:** the colleague's example project. This repo has no similar code
  to copy from; only the general method was used.

## Not changed (noticed while reading)

- `publish()` calls `table.scan(...)` once and does not follow `LastEvaluatedKey`.
  Once the table grows past one scan page (about 1 MB), `related()` will only see
  part of the library. This does not cause the 500, but it will make "similar"
  quietly wrong later.
