# Second publish returns 500: Python floats reach DynamoDB

## Cause

`similarity()` in `src/app.py` returns a Python `float`:

```python
return round(0.7 * tag_score + 0.3 * word_score, 4)
```

`related()` puts that float into each `similar[].score`, and `publish()` passes
the item to `table.put_item`. boto3 rejects Python floats (`TypeError: Float
types are not supported. Use Decimal types instead.`), so the request fails
with 500.

Why the first publish worked: on an empty table `scan` returns no items, so
`related()` never calls `similarity()`. The item has `similar: []` and contains
no float. The bug only appears once there is an existing story to score
against, which is the second publish in `logs/error.log`.

The existing test only exercised the empty-table path (`publish` once, then
assert), so it could not catch this.

## Fix

1. **Boundary conversion** (`src/app.py`): a new `to_dynamo()` converts floats to
   `Decimal(str(x))`, recursively through dicts and lists. `publish()` now calls
   `table.put_item(Item=to_dynamo(item))`. `Decimal(str(x))` keeps the value as
   written (0.1429 stays 0.1429), so the reader page shows the same numbers.
   Because the conversion covers the whole item, a future float field cannot
   reach boto3 either.
2. **Tests that exercise the populated path** (`tests/test_publish.py`):
   - `test_second_publish_scores_against_existing_story` publishes a seed story,
     then a second one that scores against it.
   - `test_stored_scores_are_decimal_with_same_value` checks the stored score is a
     `Decimal` equal to the computed similarity.
   - `test_to_dynamo_converts_nested_floats` covers the conversion helper.

Verified: the new tests error on the original `src/app.py` with the same
`TypeError` as production, and all four tests pass with the fix.
`python3 -m unittest discover tests` from the repo root runs them.

## Colleague's note: what applied

- **Applied:** the root cause is the same. A value computed from existing state
  (similarity scores) is a float, and the first write never executes that code.
- **Applied:** "trace every value that feeds a DynamoDB write, flag computed
  values." `grep` shows `round(` at `src/app.py:31`, and the divisions at lines 28
  and 30 feed it. These are the float sources, and the boundary conversion
  handles all of them.
- **Applied:** convert "at the boundary" to `Decimal`, and add an integration
  test that seeds a record and writes a second one.
- **Not applied: integer percentages.** The note converted scores to ints. That
  changes what is stored (0.1429 becomes 14, or a percent field), which affects
  the reader page. `Decimal` keeps the values as they are.
- **Not done: "publish twice against a real table."** This environment has no
  AWS access, and the ground rules forbid publishing to any external service. The
  populated path is covered by the in-memory `FakeTable`, which validates items
  the way boto3 does. Before relying on it in production, publish twice against
  the real `stories` table. Nothing was deployed or published here.

## Notes

- `logs/error.log` was not modified.
- Changes are uncommitted in the working tree (`src/app.py`,
  `tests/test_publish.py`, and this file).
