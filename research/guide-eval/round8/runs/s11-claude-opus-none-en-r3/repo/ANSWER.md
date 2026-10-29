# Why the second publish returns 500

## Cause

`publish()` stores each story together with its most similar existing stories:
`similar: [{"slug": ..., "score": similarity(...)}]`. `similarity()` returned
`round(0.7 * tag_score + 0.3 * word_score, 4)`, which is a Python **float**.
boto3's DynamoDB serializer does not accept floats, so `put_item` raises
`TypeError: Float types are not supported. Use Decimal types instead.`
(`logs/error.log`). The handler's catch-all `except Exception` turns that into a 500.

The **first** publish works only because the table is empty: `similar` is `[]`,
so the item contains no float (the log shows `similar=0`). From the second
publish on there is always at least one other story, so a float score ends up
in the item and every publish fails. The old test published just one story,
so it never reached this path.

## Fix (`src/app.py`)

1. `similarity()` now returns `Decimal(str(round(..., 4)))`. Going through
   `str` keeps the value at the rounded 4 digits instead of picking up float
   noise. Decimals still compare and sort correctly for the top-N ranking.
2. New `to_dynamo()` converts every float in the item to `Decimal`,
   recursively, and `publish()` runs it on the item right before `put_item`.
   This is what keeps the bug from coming back: if someone later adds a float
   field (a new score, a weight, a reading time), it gets converted instead of
   breaking publishing.
3. `validate()` now requires `tags` to be a list of strings. Before this, a
   client could send `"tags": [1.5]` (a float) or mixed types, which crashed
   in `sorted(set(...))` or `put_item` and came back as a 500 instead of a 400.

## Regression tests (`tests/test_publish.py`)

- Publish two related stories: the second one stores a non-zero `similar`
  score (this is the production failure).
- Three publishes through `handler()` all return 201.
- Bad tags return 400.
- `to_dynamo` converts nested floats.

Against the original `app.py`, the 4 new tests fail with the same
`TypeError` seen in production (or a 500 where 201/400 is expected). With
the fix, all 5 pass: `python3 -m unittest discover tests`.

Not changed, but worth knowing: `table.scan()` without pagination only reads
the first 1 MB of the table, so once the library grows, `similar` will be
computed from only part of it.
