# Cause

`publish()` stores related-story similarity scores in `similar[].score`. The first publish finds no existing stories, so it writes an empty list. On the second publish, `similarity()` produces a Python `float`; boto3 rejects floats while serializing the item for DynamoDB, raising `TypeError: Float types are not supported. Use Decimal types instead.` The handler catches that exception and returns 500.

# Fix

`similarity()` now returns a rounded integer percentage, which DynamoDB accepts. A regression test seeds the table through the handler, publishes a second story, and checks that the request succeeds and its stored score is an integer. This exercises the state-dependent write path that the original empty-table test missed.

Verified with `python3 -m unittest discover tests` (2 tests pass). No external table was used.
