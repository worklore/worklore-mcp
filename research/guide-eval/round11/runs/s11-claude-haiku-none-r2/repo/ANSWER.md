# Second publish returns 500: float in DynamoDB item

## Cause

`publish()` stores each story with `similar: related(story, existing)`. Each entry
in `similar` is `{"slug": ..., "score": ...}`, and `score` came from
`similarity()`, which ended with `round(..., 4)`. In Python that returns a
`float`.

DynamoDB (through boto3's `TypeSerializer`) does not accept Python floats and
raises `TypeError: Float types are not supported. Use Decimal types instead.`

The first publish works because the library is empty, so `related()` returns
`[]` and no float is ever written. The second publish is the first one with
an existing story to score against, so it puts a float into the item and
`put_item` fails. `handler()` catches the exception and returns 500.

The log matches this: the 09:14 publish (`similar=0`) returns 201, and both
09:21 and 09:22 publishes (with a neighbour to score) fail with the same
`TypeError` in `table.put_item(Item=item)`.

Reproduced locally before the change: publish one story, then a second one
with shared tags, and `publish()` raises the same `TypeError`.

## Fix

- `src/app.py`: `similarity()` now returns `Decimal(str(round(score, 4)))`
  instead of a float. The `str()` step keeps the 4-decimal value without
  binary float noise. Sorting and slicing still work because `Decimal`
  compares with `Decimal`. Added `from decimal import Decimal`.
- `tests/test_publish.py`: two regression tests.
  - `test_second_publish_with_related_stories_is_stored` publishes two related
    stories and checks that the second is stored, its `similar` entry is
    the first story, and its `score` is a `Decimal`.
  - `test_handler_second_publish_returns_201` runs the same two-publish
    sequence through `handler()` and expects 201 both times.

Both tests fail on the old `src/app.py` with the same `TypeError` and pass
with the fix. The full suite passes: `python3 -m unittest discover tests`.

## Why it won't come back

The in-memory `FakeTable` in `tests/fake_dynamo.py` already rejects floats the
way boto3 does. The old suite never reached the bug because its only test
publishes a single story, so `similar` is always empty. The new test publishes
a second story, so any float in the scored output now fails the test suite
instead of production.

Existing items are unaffected. The first story's item has `similar: []`, and no
data migration is needed.
