# Cause

The first publish finds no existing stories, so `similar` is empty and the item contains no similarity scores. On the second publish, `related()` adds a score returned by `similarity()`. That score is a Python `float` nested in `similar`. Boto3's DynamoDB serializer rejects floats, so `put_item` raises `TypeError` and the handler returns 500.

# Fix

Convert each computed score to `Decimal` before adding it to the item. This preserves the existing 0–1 score and four-decimal-place rounding while giving DynamoDB a supported numeric type. A regression test publishes two stories through the handler against the validating fake table, checks that both requests return 201, and confirms the second item's stored score is a `Decimal`. The test reproduced the 500 before the fix.
