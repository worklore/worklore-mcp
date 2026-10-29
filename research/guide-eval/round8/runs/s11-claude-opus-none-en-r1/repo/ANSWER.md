# Why the second publish returns 500

## Cause

`publish()` stores each story with its three most similar existing stories,
`similar: [{slug, score}]`. The score comes from `similarity()`, which returned
`round(0.7 * tag_score + 0.3 * word_score, 4)`. That is a Python **`float`**.
boto3's DynamoDB serializer refuses floats:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

- **First publish:** the table is empty, so `similar == []` and the item holds
  no float (`published_at` is an `int`). It gets stored with a 201
  (`similar=0` in the log).
- **Every publish after that:** there is at least one existing story, so
  `similar` holds a `{"score": <float>}`. `put_item` raises `TypeError`, and
  `handler()` turns it into a 500. A score of zero is still `0.0`, a float, so
  every publish fails once the library is non-empty, even with no overlap.

The existing test missed it because it publishes one story into an empty
table, which is the one case that never makes a score.

## Fix (`src/app.py`)

1. **At the source:** `similarity()` now returns
   `Decimal(str(round(..., 4)))`. Going through `str` gives an exact value like
   `Decimal('0.4123')` instead of a long binary-float expansion.
2. **At the storage boundary:** a new `to_dynamo()` recursively turns any
   `float` into a `Decimal`. `publish()` runs it on the whole item just before
   `put_item`. If a future field (or a client sending a number in `tags`) adds
   a float, it can no longer cause a 500. This step is what stops the bug from
   coming back.

## Regression tests (`tests/test_publish.py`)

- `test_second_publish_stores_similar_scores` sends three publishes through
  `handler()` against the boto3-faithful `FakeTable`. It checks that each one
  returns 201 and that the stored scores are `Decimal`s with the right ranking.
  Against the old `app.py` this test fails with the exact production
  `TypeError`.
- `test_to_dynamo_converts_nested_floats` checks the converter on nested
  dicts and lists.

Run: `python3 -m unittest discover tests` (3 tests pass).
