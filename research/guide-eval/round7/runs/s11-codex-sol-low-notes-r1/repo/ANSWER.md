# Cause

`related()` stored similarity scores as Python `float` values. The first publish scanned an empty table, so its `similar` list contained no scores and the write succeeded. On the second publish, an existing story produced a score; boto3's DynamoDB serializer rejected the float during `put_item`, causing the 500 shown in `logs/error.log`.

# Fix

Convert each rounded similarity score to `Decimal` when building the stored `similar` entries. This keeps the existing four decimal place score behavior while giving DynamoDB a supported numeric type. A regression test now publishes two stories through the handler using the validating fake table and checks that the second request succeeds and stores a `Decimal` score.

Verified with `python3 -m unittest discover tests -v` (2 tests pass).
