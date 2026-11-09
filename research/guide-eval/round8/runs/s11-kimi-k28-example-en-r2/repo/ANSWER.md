# Why the second publish returned 500 — cause and fix

## Cause

`similarity()` in `src/app.py` returned a Python `float` (`round()` of a blend of
two divisions). The `similar` list it feeds goes straight into
`table.put_item(Item=...)`, and boto3's DynamoDB serializer rejects floats with
exactly the error in `logs/error.log`:

    TypeError: Float types are not supported. Use Decimal types instead.

The bug only shows up on the second write because of existing state: on the
first publish the table is empty, so `related()` returns `[]` and no float ever
reaches the item — matching the log line `similar=0` on the successful 201.
From the second publish on, there is at least one existing story, scores get
computed, and every `put_item` fails during client-side serialization (the
request never reaches DynamoDB). This is a state-dependent code path
(similarity scoring) that the empty-database test never exercised.

## Fix

Convert the score to `Decimal` at the boundary, in `similarity()`
(`src/app.py:31`):

```python
return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
```

`Decimal(str(...))` keeps the existing 4-decimal rounding behavior and avoids
`Decimal(float)` representation artifacts (e.g. `Decimal(0.2965)` would carry
binary-float noise; `Decimal("0.2965")` is exact). DynamoDB accepts ints,
strings, and Decimals, so no other item field needed changes.

To make sure the bug cannot come back, the test suite now covers the populated
path: `test_publish_with_existing_story_stores_similar_scores` in
`tests/test_publish.py` seeds the table with one record, publishes a second
story, and asserts the stored `similar` entries carry `Decimal` scores — the
exact input the fake table (and real boto3) would reject as floats.

Verified:
- `python3 -m unittest discover tests` — 2 tests pass.
- End-to-end through `handler()`: first publish 201, second publish 201 with
  `similar: [{'slug': 'why-my-cron-ran-twice', 'score': Decimal('0.2965')}]`.

## Which parts of the colleague's note applied

Applied:
- The root cause is identical: floats are not valid DynamoDB values and must be
  converted to `Decimal` at the boundary.
- The explanation of why the first write survived (empty table → no computed
  scores → no floats) matches this case exactly, down to the `similar=0` log
  line.
- The core practice: add a test that seeds the table with one record and then
  writes a second one, so state-dependent code (here, similarity scoring)
  actually executes under test. That test is now in `tests/test_publish.py`.

Adapted, not taken literally:
- The note's fix was "scores became integer percentages." Here scores stay
  fractional (Jaccard blend rounded to 4 decimals), so the conversion is to
  `Decimal(str(round(...)))` instead of `int`.

Ignored:
- "publish twice against a real table" — the repo's ground rules forbid
  touching external services, and `tests/fake_dynamo.py` already validates
  items the way boto3's TypeSerializer does, so it reproduces the rejection
  faithfully.
