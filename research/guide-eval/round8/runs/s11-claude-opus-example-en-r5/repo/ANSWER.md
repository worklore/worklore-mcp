# Why the second publish returns 500

## Cause

`publish()` stores each story with its top-3 related stories:
`similar: [{slug, score}]`. The `score` comes from `similarity()` in
`src/app.py`. It's a Jaccard ratio built with `/` and passed through `round(..., 4)`,
so it's always a Python `float`, even when it's `0.0`. boto3 won't serialize
floats for DynamoDB: `TypeError: Float types are not supported. Use Decimal types instead.`
`handler()` catches this as a generic exception and returns 500.

The first publish worked because the table was empty. `related()` had nothing to
score, so `similar` was `[]` and the item had no floats in it (the log shows `similar=0 stored`).
From the second publish on, there's always at least one existing story, so
there's always at least one float score, and every publish fails. Both later
requests in `logs/error.log` fail the same way at `app.py` line 63 (`table.put_item`).

The tests didn't catch it because the only test publishes one story to an
empty table. That's the one path that never builds a score.

## Fix

1. **Conversion at the storage boundary** (`src/app.py`). The new `to_dynamo()`
   goes through the whole item recursively and turns every `float` into
   `Decimal(str(f))`. `publish()` runs every item through it right before
   `put_item`. Because it covers the whole item and not just `score`, a float
   field added later (e.g. a reading-time average) is converted too. That's the
   "can't come back" part. Going through `str()` stores `0.1234` exactly, not
   its binary expansion. Scores keep their 4-decimal precision, so the
   "related" ordering doesn't change.
2. **Tests for the populated table** (`tests/test_publish.py`):
   - `test_second_publish_with_existing_stories` seeds one story, then publishes
     a second through `handler()`. It checks for a 201, that the related story
     is there, and that its score is a non-zero `Decimal`.
   - `test_many_publishes_all_succeed` runs six publishes in a row.
   - `ToDynamoTest` checks the conversion for nested dicts and lists, and that ints, strings
     and bools are left alone.

   I checked that these tests fail against the old `app.py` (2 failures,
   1 error) and pass with the fix: `python3 -m unittest discover tests` gives 4 OK.
   `tests/fake_dynamo.py` already rejects floats the way boto3 does, so the
   tests catch the real failure without AWS.

Items already in the table don't need changing. The one bad write never
happened, and the first item has `similar: []`. When boto3 reads numbers back it
returns them as `Decimal`, which sorts and compares fine.

## Which parts of the colleague's note applied

- **Applied:** the diagnosis. A computed float (here `round()` of a division)
  reaches `put_item`, and the empty table skips the code that creates it. Also
  applied: "convert at the boundary", and adding a test that seeds a record and
  then writes a second one. That test is the main safeguard against this
  coming back.
- **Applied with changes:** the note turned scores into integer percentages. I
  used `Decimal` instead, so the 4-decimal scores keep their precision and the
  ranking order stays the same. I also convert the whole item, not one field.
- **Not done:** "publish twice against a real table". The ground rules say not
  to deploy or touch external services, so I used the boto3-equivalent fake
  table instead. Running that check against a real table after deploying is
  still a good idea.
- **Not relevant:** the general "grep for `round(` and `/`" sweep. There's only
  one write path (`publish`), and `to_dynamo` now covers all of it. `published_at` was
  already an `int`.
