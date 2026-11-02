# Why the second publish failed

`publish()` stores related stories with a similarity score. On the first publish, the table is empty, so `similar` is an empty list and the write succeeds. On the second publish, `similarity()` calculated a Python `float` and placed it in `similar[0].score`. Boto3's DynamoDB serializer rejects floats, producing the `TypeError: Float types are not supported. Use Decimal types instead.` shown in `logs/error.log`; the handler returned 500.

# Fix

`similarity()` now uses `Decimal` for its ratios and weights, and returns a `Decimal` rounded to four places. This preserves the existing 0–1 score scale while making the stored value valid for DynamoDB.

The regression test publishes two stories through the handler into a table that validates DynamoDB types. It checks that both requests return 201, the second item is stored with a related story, and its score is a `Decimal`. Before the fix, that test reproduced the 500. After the fix, `python3 -m unittest discover tests -v` passes both tests.
