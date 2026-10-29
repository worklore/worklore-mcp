# Second publish returns 500

## Cause
`related()` in `src/app.py` puts a Python `float` (`score`, from `similarity()`) into the item's `similar` list.
boto3's DynamoDB serializer rejects floats (`TypeError: Float types are not supported. Use Decimal types instead.`),
so `put_item` fails and the handler returns 500.

The first publish worked only because the table was empty: `similar` was `[]`, so there were no floats.
Every publish after that has at least one existing story, so it carries a float score and fails.
The old test only published one story into an empty table, so it never hit this.

## Fix
- `related()` now stores `Decimal(str(score))` (via `str` so the stored value is the rounded 4-digit number, not a binary float expansion).
- Added `test_second_publish_with_similar_stories`, which publishes two stories. The fake table rejects floats the way boto3 does, so a float would fail this test.

## Not changed
`publish()` reads existing stories with a single `scan`, which returns at most 1 MB per call.
Once the library is larger than that, `similar` will only be computed from part of it.
