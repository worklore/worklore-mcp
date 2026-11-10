# Second publish returns 500

## Cause

`similarity()` in `src/app.py` returned a Python `float` (`round(..., 4)`).
`publish()` stores those scores in `item["similar"]` as `[{slug, score}]`, and
`table.put_item()` hands the item to boto3. boto3's DynamoDB serializer rejects
Python floats (`TypeError: Float types are not supported. Use Decimal types
instead.`), so the write fails and `handler()` turns the exception into a 500.

Why only the second publish: `similar` is built from the stories already in the
table. The first publish scans an empty table, so `similar` is `[]` and no float
is ever serialized. The second publish has one existing story to score against,
so it produces a float and fails. This matches `logs/error.log`: the first
publish is `similar=0 stored` (201), and both failures come right after the
first success.

## Fix

- `src/app.py`: `similarity()` now returns `Decimal`. It goes through `str()`
  first (`Decimal(str(round(x, 4)))`) so the value is exactly `0.25`, not the
  binary float expansion `Decimal(0.25)` would give for other values.
- `tests/test_publish.py`: regression tests so this cannot come back silently:
  - `test_second_publish_with_related_story_succeeds`: publishes two related
    stories and checks the second one is stored with a `similar` entry.
  - `test_handler_second_publish_returns_201`: the same flow through `handler()`,
    checking the HTTP-style status codes.
  - `test_similarity_scores_are_dynamo_safe`: checks the score is a `Decimal`
    with the expected value.

`FakeTable` already rejects floats the way boto3 does, so the tests fail for the
same reason production did. Against the original code, the new tests produce
1 error and 2 failures. With the fix, all 4 tests pass
(`python3 -m unittest discover tests`).

## Not changed

- Nothing was deployed or published. This only changes the repo.
- `logs/error.log` is untouched.
