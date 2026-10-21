# Why the second publish returns 500

## Cause

`similarity()` in `src/app.py` returned a Python `float`, from
`round(0.7 * tag_score + 0.3 * word_score, 4)`. That score is stored in
`item["similar"][i]["score"]`, and boto3's DynamoDB serializer rejects floats:

    TypeError: Float types are not supported. Use Decimal types instead.

The first publish succeeds because the table is empty. `related()` never calls
`similarity()`, so no float reaches `put_item`. Every later publish has existing
stories to compare against, so it writes a float and fails. `handler()` catches
the exception and returns 500, which matches `logs/error.log`.

The existing test only published into an empty `FakeTable`, so it never reached
the code path that writes a score. It passed while the bug was live.

## Fix

- `src/app.py`: `similarity()` now returns `Decimal(str(round(..., 4)))`. This
  keeps the same 0-1 score with four decimals, and the value is `Decimal`, which
  is the type DynamoDB stores and returns on reads. The `Decimal` import was added.
  `handler()` only returns the slug in its JSON response, so `Decimal` cannot break
  `json.dumps`.

## Keeping it from coming back

- `tests/test_publish.py`:
  - `test_second_publish_with_related_stories_is_stored` publishes twice and
    checks that the second story's `similar` list contains the first story.
  - `test_handler_returns_201_on_second_publish` checks the HTTP-level result of
    the second publish.
  Both failed before the fix (500 != 201) and pass now.
- `tests/fake_dynamo.py` already rejects floats the way boto3 does, so any future
  float written to the fake table fails the test suite.

Run with `python3 -m unittest discover tests` from the repo root.

## Not done

- Nothing was deployed, published or sent anywhere. The fix has only been
  verified against `FakeTable`, not a real DynamoDB table.
- The changes are not committed.
