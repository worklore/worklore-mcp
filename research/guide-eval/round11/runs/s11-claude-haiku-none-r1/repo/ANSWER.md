# Answer: second publish returns 500

## Cause

`similarity()` returns a Python `float` (`round(..., 4)`), and `related()` stores that
float as `similar[].score`. `publish()` then calls `table.put_item(Item=item)` with
that float inside the item.

- The first publish succeeds because the library is empty, so `similar` is `[]` and
  there is no float to store.
- The second publish finds one existing story, so `similar` contains
  `{"slug": ..., "score": 0.xxxx}`. boto3's DynamoDB serializer rejects floats with
  `TypeError: Float types are not supported. Use Decimal types instead.`
- `handler()` catches the exception in its generic `except Exception` branch,
  logs it, and returns 500. That matches `logs/error.log`: the 09:21:47 and
  09:22:10 failures are the two publishes after the first one, and both show the
  same `TypeError` at `put_item`.

The existing test only published once against an empty table, so it never reached
the float path.

## Fix

- `src/app.py`: added `to_dynamo()`, which recursively converts every `float` in the
  item to `Decimal(str(value))`. `str` keeps the value exact (`0.1` becomes
  `Decimal('0.1')`, not the binary-float expansion). `publish()` now calls
  `table.put_item(Item=to_dynamo(item))`. The conversion sits at the write boundary,
  so future float fields are also covered.
- `tests/test_publish.py`:
  - `test_second_publish_with_related_stories_succeeds` publishes twice through
    `handler()`, expects 201, and checks that the stored score is a `Decimal` equal
    to the computed similarity. This is the scenario that failed in production.
  - `test_floats_are_converted_to_decimal_exactly` checks the conversion helper,
    including nested lists and dicts.

## Verification

- Before the fix, a two-publish reproduction against `tests/fake_dynamo.py` returned
  500 with the same `Float types are not supported` error as the log.
- After the fix, `python3 -m unittest discover tests` passes all 3 tests, and the same
  reproduction returns `201`.

Nothing was deployed, published, or sent to any external service. The changes are
uncommitted in the working tree.
