# Why the second publish returns 500

## Cause

`publish()` stores each story with `similar: [{slug, score}]`, and the score
came from `similarity()`, which returned `round(0.7 * tag + 0.3 * word, 4)`.
That is a Python **float**. boto3's DynamoDB serializer rejects floats anywhere
in an item:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

(see `logs/error.log`, raised from `table.put_item` in `publish`).

- **First publish:** the table is empty, so `similar == []` and the item has no
  floats. It succeeds (`similar=0 stored`, 201).
- **Every later publish:** there is now at least one existing story, so
  `similar` has a float `score`. `put_item` raises `TypeError`, and `handler`
  turns that into a 500.

The only test published a single story into an empty table, so it never
exercised a non-empty `similar` list.

## Fix (`src/app.py`)

1. **At the source:** `similarity()` now returns
   `Decimal(str(round(..., 4)))`. Going through `str` gives an exact 4-place
   decimal such as `Decimal('0.4429')`, not the float's binary expansion.
   Sorting and comparing still work as before.
2. **At the write boundary, so it can't come back:** a new `to_dynamo()` helper
   recursively converts any float to `Decimal`, and `publish()` sends the item
   through it right before `put_item`. A float added to the item later (a new
   field, a changed formula) gets converted instead of causing another 500.

## Regression tests (`tests/test_publish.py`)

- `test_second_publish_stores_float_free_scores`: publishes two related
  stories and checks the second one stores with a non-empty `similar`. This is
  the exact production failure.
- `test_handler_returns_201_for_every_publish`: five publishes through
  `handler`, and each one must return 201.
- `test_to_dynamo_converts_nested_floats`: checks the boundary helper on
  nested dicts and lists.

`tests/fake_dynamo.py` already rejects floats the same way boto3 does. Before
the fix the new tests fail with that `TypeError`; after it, all 4 tests pass
(`python3 -m unittest discover tests`).

## Side note (not the cause of this bug)

`table.scan()` returns at most 1 MB per call, and `publish` doesn't follow
`LastEvaluatedKey`. Once the library is large, `similar` will be computed from
only part of it. This won't cause a 500, but it's worth paginating (or
precomputing) later.
