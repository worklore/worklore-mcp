# Why the second publish returns 500

## Cause

`similarity()` in `src/app.py` returns a Python `float` (`round(..., 4)`).
`related()` puts that value in each `similar` entry as `score`, and `publish()`
passes the whole item to `table.put_item`. boto3 rejects Python floats:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The first publish succeeds because the table is empty. `related()` has nothing
to compare against, so no `score` float is ever built. The second publish finds
one story, computes a score, and the write fails. The log shows exactly this:
the first publish is `similar=0 stored` and the second is the `TypeError` with
a 500 (`logs/error.log`).

The existing test only published into an empty `FakeTable`, so it never reached
the float. The fake table already rejected floats, so the gap was the test data,
not the fake.

## Fix

1. **`src/app.py`: `to_dynamo()` converts every float to `Decimal(str(value))`
   recursively, and `publish()` calls it on the item right before `put_item`.**
   `str()` keeps the value as written (`0.4667` stays `0.4667`). Because the
   conversion covers the whole item, a float from any future scoring, averaging
   or division path cannot reach the write. A single-field fix would leave that
   gap open.
2. **`tests/test_publish.py`:**
   - `test_publish_into_populated_table` seeds one story and then publishes a
     second, so the score write runs. It also checks that the stored score is a
     `Decimal`.
   - `test_handler_publish_into_populated_table` does the same through
     `handler()`, the endpoint path that returned 500.
   - `test_to_dynamo_converts_nested_floats` covers the conversion, including
     floats nested in lists and dicts.

Verified: the new tests fail on the original `app.py` (1 failure, 2 errors) and
all 4 pass with the fix (`python3 -m unittest discover tests`).

## What the colleague's note did and did not apply to

- **Applied: the populated-table test.** The empty-table path hid the bug, so
  the write-path tests now seed one record first.
- **Applied: the general rule that any computed float can reach the write.**
  That is why the fix converts at the write boundary rather than only at the
  `score` line.
- **Not applied: integer percentages.** The README defines `similar` as
  `[{slug, score}]` with a 0–1 ratio. Changing it to percentages would change
  the stored contract for readers and lose precision. `Decimal` keeps the
  existing meaning.
- **Not applied: "one-line change."** That one-liner was for their scores. Here
  the converter has to cover the whole item to stop the same class of error.

## Not done

- Nothing was deployed, published or sent to any service. The 500s are from the
  production log; the fix has only been checked with the fake table and the
  unit tests.
- The change is not committed.
- Existing items in DynamoDB are unaffected: the failed writes never stored
  anything.
