## Cause

The `similarity()` function in `src/app.py` returns a Python `float` (via `round(..., 4)`).
When a second story is published, the `related()` function builds a list of similar stories
with their `score` values (the float returned by `similarity()`). DynamoDB rejects
float values in items, raising:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The first publish succeeds because the `similar` list is empty (no existing stories to
compare against). The second publish fails because `similar` now contains entries with
float `score` values.

## Fix

Changed `src/app.py`:

1. Added `from decimal import Decimal` at the top of the file.
2. Modified `similarity()` to return `Decimal(str(round(...)))` instead of a float.

This ensures the `score` field stored in DynamoDB is a `Decimal` type, which is
supported by DynamoDB and will never trigger the float rejection error.
