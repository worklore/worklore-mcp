# Why the second publish returns 500

## Cause

`publish()` stores each story together with `similar: [{slug, score}]`, and
`score` comes from `similarity()`, which returns a Python `float`
(`round(0.7 * tag_score + 0.3 * word_score, 4)`). boto3's DynamoDB serializer
doesn't accept `float` anywhere in an item. It raises
`TypeError: Float types are not supported. Use Decimal types instead.` That
error isn't a `ValueError`, so `handler()` catches it as a generic exception
and returns 500.

The first publish works only because the library is empty. `scan()` returns
nothing, so `similar == []` and the item contains no floats (`published_at` is
an `int`). The log confirms it: `similar=0 stored`. From the second publish on
there is at least one other story, so `similar` holds a float score and
`put_item` fails every time (09:21:47 and 09:22:10 in `logs/error.log`).

The existing test missed this because it only publishes into an empty table.

## Fix (`src/app.py`)

- New `to_dynamo()` function. It walks the item recursively and converts every
  `float` to `Decimal(str(value))`. Going through `str` keeps the short form
  (`0.4667`) instead of the binary expansion. `NaN`/`inf` are rejected with a
  `ValueError` (→ 400), because DynamoDB can't store them either.
- `publish()` runs the item through `to_dynamo()` right before
  `table.put_item()`. The conversion happens at the database boundary rather
  than inside `similarity()`, so any float field added to the item later is
  converted automatically. That's what keeps this class of error from coming
  back.
- Items read back from DynamoDB already contain `Decimal`. They're only passed
  to `similarity()`, which uses `slug`, `tags` and `body`, not `score`, so the
  read path is unaffected.

## Tests (`tests/test_publish.py`)

- `test_second_publish_stores_float_free_similar` publishes 3 stories in a row
  through `handler()`. It checks that every call returns 201 and that
  `similar[].score` is stored as a `Decimal`. On the old code it fails with
  `500 != 201`, the same `TypeError` as in production.
- `test_to_dynamo_converts_nested_floats` checks the conversion of nested
  floats, and that `bool`/`int` values are left unchanged.

`python3 -m unittest discover tests`: all 3 tests pass.
