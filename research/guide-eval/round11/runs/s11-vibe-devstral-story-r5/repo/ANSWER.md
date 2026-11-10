# Cause and Fix for Second Publish 500 Error

## Cause

The `similarity()` function in `src/app.py` computes similarity scores using Python's division operator (`/`), which produces `float` values. These float scores are then stored in the `similar` list within DynamoDB items. DynamoDB (via boto3) rejects float values with the error: `TypeError: Float types are not supported. Use Decimal types instead.`

The first publish succeeds because the table is empty, so `related()` returns an empty list with no scores to store. The second publish fails because there's now at least one existing story, so `related()` computes similarity scores (as floats) and attempts to store them, triggering the DynamoDB error.

This matches the colleague's note exactly: "my 'it works' test had only ever exercised the empty-database path. Any code whose behavior depends on existing state — scoring, deduplication, aggregation, 'related items' — has a second code path that first-write tests never touch."

## Fix

Changed `src/app.py`:

1. Added import: `from decimal import Decimal, ROUND_HALF_UP`
2. Modified `similarity()` to use `Decimal` arithmetic throughout:
   - Convert all numeric values to `Decimal` before division
   - Use `Decimal("0.7")` and `Decimal("0.3")` for the weighting factors
   - Use `.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)` instead of `round(..., 4)` to maintain Decimal type

This ensures all similarity scores are `Decimal` objects, which DynamoDB accepts.

Also added a test case in `tests/test_publish.py` (`test_publish_with_existing_story`) that seeds the table with one story before publishing a second one, ensuring the state-dependent code path (computing and storing similarity scores) is tested.

## Parts of the colleague's note that applied

- The DynamoDB float type error: **Applied** — exact same error message
- The empty-database path explanation: **Applied** — first publish works, second fails
- The fix approach (convert floats to Decimal): **Applied** — used Decimal arithmetic
- The test improvement (seed table before second write): **Applied** — added test case
- The verification steps (grep for round( and /): **Applied** — found the problematic code

## Files changed

- `src/app.py` — Fixed `similarity()` to use Decimal arithmetic
- `tests/test_publish.py` — Added test for populated-table path
