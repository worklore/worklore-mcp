# Second publish returns 500: Python floats written to DynamoDB

## Cause

`similarity()` in `src/app.py` returns `round(0.7 * tag_score + 0.3 * word_score, 4)`,
which is a Python `float`. `related()` copies that value into each entry of
`similar` as `score`, and `publish()` passes the item to `table.put_item`.
boto3's DynamoDB serializer rejects floats:

    TypeError: Float types are not supported. Use Decimal types instead.

The bug only runs when the table already holds a story:

- First publish: the table is empty, `existing` is `[]`, `similar` is `[]`.
  No score is ever built, so no float reaches the write. The log confirms it
  (`similar=0 stored`, 201).
- Second publish: `existing` has one story, `related()` builds a score, and the
  float goes into `similar`. The write fails (500).

The existing test (`test_publish_stores_story`) only publishes into an empty
`FakeTable`, so it never reaches the scoring path. The fake table already
rejects floats, so the test would have failed if it had seeded one story.

## Fix

1. **Write-boundary conversion (`src/app.py`).** A new `to_dynamo()` converts
   every float in the item to `Decimal(str(value))` recursively, and `publish()`
   calls it right before `put_item`. Any float produced anywhere in the item,
   present or future, is converted, not only the score. `str()` keeps the digits
   exactly (`0.5` stays `Decimal('0.5')`).
2. **Score semantics unchanged.** The score stays a 0–1 ratio. Readers still get
   the same numbers, just stored as Decimal.
3. **Tests that exercise the populated path (`tests/test_publish.py`).**
   - `test_second_publish_into_populated_table`: seeds one story, publishes a
     second, and checks that `similar` has the first story with score `0.5`.
   - `test_handler_returns_201_when_table_is_populated`: the HTTP-level
     regression, two publishes through `handler()`, both expect 201.
   - `test_to_dynamo_converts_nested_floats`: checks the conversion for nested
     dicts and lists.

Verified: the new tests fail with `src/app.py` reverted (2 errors, 1 failure) and
all 4 pass with the fix. `python3 -m unittest discover tests` is green. I
reproduced the production error with a seeded `FakeTable` before the change.

Not done: I did not deploy or publish anything. The fix needs a deploy to reach
the Lambda, and the production log can only confirm it after that.

## Colleague's note: what applied

- **Applied:** the empty-table path hid the bug, because no score is computed
  until a story exists. The production log matches (`similar=0` on the first
  publish).
- **Applied:** write-path tests must seed the table with at least one record
  first. That is the new `test_second_publish_into_populated_table`, plus the
  handler test.
- **Applied:** the error message is the same, and it comes from boto3's
  serializer.
- **Not applied:** the one-line change to integer percentages. Our score is a
  0–1 ratio, and switching to integer percentages would change the value
  readers receive. Decimal keeps the value and fixes the type. The note's
  statement that DynamoDB accepts ints and Decimals is true, but it's not needed
  here.
- **Not applied:** the note's "divisions, averages and rounded scores" list
  describes its own code. Here the only float source is `similarity()`. The
  write-boundary conversion covers the others anyway.
