# Root Cause and Fix

## Cause

The `similarity()` function in `src/app.py` returns a Python `float` (via `round(..., 4)`). When a second story is published, the `related()` function computes similarity scores against existing stories and stores them in the `similar` list as floats. DynamoDB (via boto3) rejects float values with:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The first publish succeeds because there are no existing stories, so `related()` returns an empty list `[]` with no scores. The second publish fails because it tries to store a float score for the first story.

## Fix

Changed `src/app.py`:

1. Added `from decimal import Decimal` import
2. Modified `similarity()` to return `Decimal(str(round(...)))` instead of a raw float

This ensures the score stored in DynamoDB is a Decimal type, which is the only numeric type DynamoDB accepts for non-integer values.

## Changed File

- `src/app.py`: Added Decimal import and converted similarity return value to Decimal
