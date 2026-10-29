# Second publish returns 500

## Cause

`publish()` stores each story together with its related stories,
`similar: [{slug, score}]`. `similarity()` returned
`round(0.7 * tag_score + 0.3 * word_score, 4)`, which is a Python `float`.
boto3's DynamoDB serializer rejects floats:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

(See `logs/error.log`, which points at `table.put_item(Item=item)` in `publish`.)

The first publish worked only because the table was empty: there were no
neighbours, so `similar` was `[]` and the item held no floats. From the second
publish on there is always at least one existing story, so the item contains a
float score and `put_item` raises. `handler` catches the exception and returns
500. Every publish after the first fails the same way.

The existing test published only one story into an empty table, so it never
touched this code path.

## Fix (`src/app.py`)

1. **The source:** `similarity()` now returns
   `Decimal(str(round(..., 4)))`. Going through `str` keeps the short value
   (e.g. `0.4167`) and avoids boto3's `Inexact` error, which you can get from
   `Decimal(float)`.
2. **The boundary, so it can't come back:** a new `to_dynamo()` helper
   recursively turns every `float` in the item (including nested dicts and
   lists) into a `Decimal`. `publish()` runs every item through it right
   before `put_item`. If a float field is added later (a new score, a reading
   time, etc.), it gets converted instead of causing a 500.

## Regression tests (`tests/test_publish.py`)

- `test_second_publish_stores_similar_scores` sends three stories through
  `handler` into the same table. The second one is the case that failed in
  production, and the third has no tags. It checks that every response is 201
  and that the stored `similar[0].score` is a `Decimal` greater than 0.
- `test_to_dynamo_converts_nested_floats` covers the boundary helper.

Against the old `src/app.py`, the first test fails with `500 != 201`, the same
error as in production. With the fix, all 3 tests pass
(`python3 -m unittest discover tests`).

## Side note (not changed)

`publish()` reads only the first page of `table.scan()`. Once the table goes
over 1 MB, related stories will be picked from part of the library only. This
doesn't cause the 500, but if it matters, handle `LastEvaluatedKey`.
