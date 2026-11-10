## Cause

The `similarity()` function returns a float value (via `round(value, 4)`), which gets stored in the `similar` list as `{"slug": ..., "score": float}`. DynamoDB does not accept Python float types — it requires `Decimal` for numeric values. The first publish succeeds because there are no existing stories, so `related()` returns an empty list. The second publish fails because it tries to store float scores for the related stories.

## Fix

Changed `src/app.py`:

1. Added `from decimal import Decimal` import
2. Modified `similarity()` to return `Decimal(str(round(...)))` instead of a float

This ensures the score values are DynamoDB-compatible Decimal types, preventing the 500 error on subsequent publishes.
