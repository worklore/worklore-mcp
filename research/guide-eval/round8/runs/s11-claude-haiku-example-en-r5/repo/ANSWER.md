# Second publish returns 500: float in a DynamoDB write

## Cause

`logs/error.log` shows `TypeError: Float types are not supported. Use Decimal types instead.`
raised from `table.put_item(Item=item)` in `publish()` (`src/app.py`).

The float comes from `similarity()`:

```python
return round(0.7 * tag_score + 0.3 * word_score, 4)   # a Python float
```

`related()` puts that value into each `similar` entry as `score`, and `publish()` passes the
whole item to `put_item`. boto3 refuses Python floats.

Why the first publish worked: on the first publish the table is empty, so `related()` has no
existing stories to compare against, `similar` is `[]`, and no float ever reaches DynamoDB.
The second publish is the first one that scores anything, so it is the first to fail. The bug
exists only once the table has data.

Why the tests missed it: `tests/test_publish.py` only publishes into an empty `FakeTable`, so
the scoring path never ran. The fake does reject floats, but nothing in the suite ever gave it
a float to reject.

## Fix

1. **`src/app.py`: convert at the write boundary.** A new `to_dynamo()` walks the item
   recursively and converts every `float` to `Decimal(str(value))`. `publish()` now calls
   `table.put_item(Item=to_dynamo(item))`. Using `str()` keeps the four decimal places that
   `round(..., 4)` produced, without binary float noise. The score scale stays the same
   (0–1), so nothing downstream changes meaning. Because the conversion is applied to the whole
   item, a future float (an average, a count ratio) cannot reach DynamoDB by the same route.
2. **`tests/test_publish.py`: cover the populated path.**
   - `test_second_publish_with_related_story_stores` seeds one story, publishes a second one,
     and checks the `similar` score is stored as a `Decimal`. It fails on the old code with the
     same `TypeError`.
   - `test_handler_seeded_table_three_publishes` runs four publishes through `handler()` and
     expects 201 each time.
   - `test_to_dynamo_converts_nested_floats` checks the converter on nested dicts and lists.

Verified: on the original `app.py` the new tests fail (two failures, one error, all
`TypeError`); with the fix all four tests pass (`python3 -m unittest discover tests`).

## Reading the colleague's note

- **Applied: the root cause pattern.** A value computed from existing state (here the
  similarity score) is a float on the populated path and never on the first write. This is the
  same bug.
- **Applied: convert at the boundary to `Decimal`.** This is the fix used here. The note's
  alternative (integer percentages) was not used because it changes the score's meaning in the
  stored data, and the reader page's expectations are not in this repo.
- **Applied: seed a record, then write a second one.** That is the regression test added above.
- **Applied: grep for float sources.** `grep -rn "round(\| / \|//" src/` finds three float
  sources, all in `similarity()` (lines 27, 29, 30). Only the `round()` result reaches a
  DynamoDB item. `published_at` is an `int`, and tags and body are strings.
- **Not applied: publish twice against a real table.** This runs against an external service.
  The ground rules say not to publish or deploy, so I did not do it. The seeded-table tests
  exercise the same path against the boto3-style fake, which rejects floats.
- **Not applied: integer percentage scores.** See above.

## Things to know after this fix

- **Reading `similar` back returns `Decimal`.** boto3 deserializes numbers as `Decimal`, so
  `score` comes back as `Decimal('0.2143')`, and `json.dumps` cannot encode it. Any reader code
  that serializes `similar` needs `default=float` or a `Decimal`-to-string step. The reader is
  not in this repo, so I did not change it.
- **Found, not fixed: `scan()` is not paginated.** `publish()` calls
  `table.scan(TableName=...)` once. DynamoDB returns at most 1 MB per page, so as the library
  grows, `related()` will silently compare against only the first page and the "related"
  stories will be wrong. This does not cause the 500. It is the same kind of state-dependent
  path that first-write tests miss, and it should get its own change with a test that seeds
  enough data to paginate.

## Files changed

- `src/app.py`: added `Decimal` import and `to_dynamo()`; `publish()` writes `to_dynamo(item)`.
- `tests/test_publish.py`: added `Decimal` import and three tests.
- `ANSWER.md`: this file.

Nothing was committed, deployed, or published.
