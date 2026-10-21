# Why the second publish returns 500

## Cause

`publish()` stores each story with its top-3 related stories, `similar: [{slug, score}]`.
`similarity()` (`src/app.py`) computes the score with `/` and `round(..., 4)`, so it is a
Python `float`. boto3 doesn't accept floats in DynamoDB items. `put_item` raises
`TypeError: Float types are not supported. Use Decimal types instead.`, and `handler()`
turns that into a 500.

The first publish worked only because the table was empty. `scan()` returned no items,
so `similar` was `[]` and the item had no floats in it (log: `similar=0 stored`, 201).
From the second publish on, there is at least one existing story to score against, so a
float ends up in the item and every publish fails. The only test published into an empty
table, so the scoring path never ran under test.

## Fix

- **Convert at the write boundary.** `to_dynamo()` in `src/app.py` walks the item and
  converts every `float` to `Decimal(str(value))`, so `0.4567` stays exactly `0.4567`.
  `publish()` runs the whole item through it right before `put_item`. That covers the
  score and also any computed number added to the item later (averages, ratios), so this
  class of bug can't come back. Non-finite values (NaN or inf, which DynamoDB rejects)
  raise a clear `TypeError` instead of being written.
- **Test the populated path** (`tests/test_publish.py`):
  - `test_second_publish_stores_similarity_scores` puts one story in the table, then
    publishes a related one. It checks that the score is stored as a non-zero `Decimal`.
  - `test_handler_publishes_twice` sends three publishes through `handler()` and expects
    a 201 for each.
  - `test_to_dynamo_converts_nested_floats` checks the converter on nested values and
    that NaN is rejected.

  Without the fix in `src/app.py`, all three new tests fail. With it, all 4 tests pass
  (`python3 -m unittest discover tests`).

## Verify against real DynamoDB

The fake table checks values the way boto3's serializer does. I didn't run anything
against AWS. To confirm in a real environment, publish two stories with overlapping tags
and check that the second one returns 201 and that its stored `similar[0].score` is a
number.
