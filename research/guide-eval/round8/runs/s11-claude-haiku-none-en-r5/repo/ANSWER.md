# Second publish returns 500

## Cause

`publish()` stores each story with `similar: [{slug, score}, ...]`. The `score`
came from `similarity()`, which returned a Python `float` (`round(..., 4)`).

- The first publish works because the library is empty, so `related()` returns
  `[]` and no float is ever written. (`logs/error.log`: `similar=0 stored`, 201.)
- The second publish has one existing story to compare against, so `similar`
  holds a float. boto3's DynamoDB serializer rejects floats with
  `TypeError: Float types are not supported. Use Decimal types instead.`
  The exception is caught by `handler()`'s generic `except`, which returns 500.

The existing test only published into an empty table, so it never reached the
float path. The fake table in `tests/fake_dynamo.py` already rejects floats the
same way boto3 does, so the bug was reproducible in tests all along; nothing
exercised it.

## Fix

`src/app.py`: `similarity()` now returns a `Decimal`, built from the rounded
float's string form (`Decimal(str(round(...)))`) so the stored value is exactly
the 4-digit score. The module imports `Decimal`, and the docstring says why.

## Keeping it from coming back

`tests/test_publish.py` gained two tests:

- `test_second_publish_with_related_story_succeeds`: publishes two overlapping
  stories through `handler()`, expects 201 on the second, and checks that the
  stored `score` is a `Decimal`. This is the path that failed in production.
- `test_similarity_is_decimal`: pins the return type of `similarity()`, so a
  future change back to float fails directly.

Verified: both new tests fail against the original `app.py` and pass with the
fix. `python3 -m unittest discover tests` is green (3 tests).

## Not done

- Nothing was deployed. The second story from the log (`09:21:47`, 500) was
  never stored and has to be published again after the fix ships.
