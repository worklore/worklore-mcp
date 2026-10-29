# Why the second publish returns 500

## Cause

`publish()` (`src/app.py`) stores each story with its top-3 related stories,
`similar: [{slug, score}]`. `score` comes from `similarity()`, which returns
`round(0.7 * tag_score + 0.3 * word_score, 4)`, and that is a Python `float`.
boto3's DynamoDB serializer rejects floats, so `put_item` raises
`TypeError: Float types are not supported. Use Decimal types instead.`
(`logs/error.log`). `handler()` turns that into a 500.

The first publish worked only because the table was empty. `scan()` returned
nothing, so `similar` was `[]` and the item held no floats (`similar=0` in the
log). Every publish after that has at least one existing story, so it computes a
score and crashes. The only existing test publishes into an empty table, so it
never ran the scoring path.

## Fix

- **Convert at the write boundary** (`src/app.py`). New `to_dynamo()` walks the
  item and turns every float, at any depth, into `Decimal(str(f))`. `publish()`
  runs it on the item just before `put_item`. Fixing only the `score` field would
  leave the next float someone adds to the item with the same crash. Converting
  every float at the boundary covers future ones too, and keeps the 4-decimal
  precision.
- **Test the populated path** (`tests/test_publish.py`):
  - `test_second_publish_with_existing_stories` seeds one story, publishes a
    second one, and checks that the stored `similar` has a positive score.
  - `test_handler_second_publish_returns_201` sends two publishes through
    `handler()` and expects 201 both times.
  - `test_to_dynamo_converts_nested_floats` covers the converter itself.

  `tests/fake_dynamo.py` already rejects floats the same way boto3 does. Against
  the original `app.py`, all three new tests fail with the error from the
  production log. With the fix, all 4 tests pass
  (`python3 -m unittest discover tests`).

## Which parts of the colleague's note applied

- **Applied:** the diagnosis. Floats from a computed similarity score crashed the
  write, and only once existing data made the scoring code run. The empty-table
  first write hid the bug. Also applied: the advice to trace computed values
  (`round(`, `/`) that feed the item, and to add a test that seeds a record
  before the write under test.
- **Changed:** the note converted scores to integer percentages. I convert to
  `Decimal` instead, applied to the whole item rather than to one field, so no
  precision is lost and any future float field is covered.
- **Not applied:** "publish twice against a real table". The ground rules forbid
  touching external services. The in-memory fake already reproduces boto3's float
  check, so the seeded test reproduces this failure. Nothing was deployed.

## Noticed, not changed

`publish()` reads the existing stories with one `scan()` and doesn't paginate
(`LastEvaluatedKey`). Once the table grows past 1 MB, related-story matching will
quietly look at only part of the library. It also scans the whole table on every
publish, so the cost grows with the library.
