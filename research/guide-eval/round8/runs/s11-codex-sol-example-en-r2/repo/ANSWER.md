# Why the second publish failed

`logs/error.log` shows `put_item` failing with `TypeError: Float types are not supported. Use Decimal types instead.` The first publish scans an empty table, so `related()` returns an empty list. On the second publish, the scan finds the first story; `similarity()` computes a Python `float` and `related()` puts it in `item["similar"][0]["score"]`. boto3 rejects that nested float while serializing the item, and `handler()` returns 500.

# Fix

`similarity()` now uses `Decimal` for both ratios and weights, then rounds to four decimal places with `quantize()`. Scores keep their existing 0–1 scale and four-place precision, and the item sent to DynamoDB contains a supported numeric type. A regression test publishes two stories through `handler()` using the local DynamoDB stand-in, checks both 201 responses, and verifies the persisted fractional score. The stand-in rejects floats as boto3 does.

# Verification

`python3 -m unittest discover tests -v` passes both tests. No external table was used.

# Colleague's note

The empty-table versus populated-table explanation, boto3's rejection of floats, and the need for a seeded write-path test applied directly. The suggested integer-percentage conversion was unnecessary here: `Decimal` fixes serialization while preserving the existing score scale and precision. Publishing twice against a real table was outside this task's local-only ground rules; the local stand-in exercised the same type check.
