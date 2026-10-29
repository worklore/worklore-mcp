# Cause

`similarity()` returns a Python `float`, and `publish()` stores those scores in
the item's `similar` list. boto3's DynamoDB serializer rejects floats
(`TypeError: Float types are not supported. Use Decimal types instead.`).

The first publish worked only because the table was empty, so `similar` was `[]`
and no float was ever written. From the second publish on, `similar` holds
scores, so `put_item` fails and the handler returns 500.

# Fix

`similarity()` in `src/app.py` now returns `Decimal(str(round(..., 4)))`.

To keep it from coming back, I added `test_second_publish_stores_similar` in
`tests/test_publish.py`. It publishes two stories, so the `similar` path runs.
The fake table rejects floats the way boto3 does. The old test only published
one story into an empty table, which is why it never caught this.
