# Second publish returns 500: float reaches DynamoDB

## Cause

`similarity()` in `src/app.py` returns `round(..., 4)`, which is a Python `float`.
`related()` puts that float into `similar[].score`, and `publish()` passes the
item to `table.put_item`. boto3's DynamoDB serializer rejects floats:

    TypeError: Float types are not supported. Use Decimal types instead.

The scoring path only runs when the table already holds a story. With an empty
table, `related()` has nothing to score, so no float is ever written. That is why
the first publish returned 201 and every later one returned 500. The log in
`logs/error.log` shows the same pattern: `similar=0 stored` for the first story,
then the TypeError on the next publish.

The existing test only used an empty `FakeTable`, so it took the path with no
floats and passed.

## Fix

`src/app.py` now has `to_dynamo(value)`, which recursively converts every float
to `Decimal(str(value))` (`str` avoids binary artifacts such as `0.1 + 0.2`).
`publish()` calls it at the write boundary:

    table.put_item(Item=to_dynamo(item))

Converting at the boundary covers every path that can produce a float (scores,
averages, ratios), not only the one that happened to run first. Scores keep their
0–1 meaning with four decimal places; `similar[].score` is now stored as a
`Decimal` such as `Decimal("0.4667")`.

## Tests

`tests/test_publish.py` gained tests that seed the table with one existing story
before the write, so the scoring path runs:

- `test_publish_with_existing_story_stores_scores`: publish against a populated table.
- `test_handler_second_publish_returns_201`: the HTTP-level path returns 201, not 500.
- `test_scores_are_stored_as_decimal_not_float`: the stored score is a `Decimal` with the expected value.
- `test_to_dynamo_converts_nested_floats`: nested floats are converted and other types are untouched.

Before the fix, the three write-path tests failed with the same TypeError. After
the fix, all five tests pass (`python3 -m unittest discover tests`).

## Colleague's note: what applied

- **Applied:** the diagnosis. The empty-table path hid the bug, and the scoring path
  that runs only with existing data put a float into the write.
- **Applied:** seeding the table with one record in write-path tests so the populated path runs.
- **Not applied:** converting scores to integer percentages. That changes the stored
  value from a 0–1 ratio to a 0–100 integer, which is a data-contract change that
  `README.md` and the readers would need to agree on. `Decimal` fixes the error
  without changing what the score means. The colleague's fix is valid for their
  case; it is not needed here.
- **Not applied:** the one-line fix. A single conversion at the call site would
  pass the test but would leave every other float path open. The boundary
  conversion is what keeps this from coming back.

## Notes

- Nothing was deployed, published or sent anywhere. Changes are uncommitted in the working tree.
- Records that failed on the second publish were never written, so the table has no float data to clean up.
