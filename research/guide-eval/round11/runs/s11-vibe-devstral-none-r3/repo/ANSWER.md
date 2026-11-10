## Cause

The `similarity()` function in `src/app.py` returns a Python `float` (via `round(value, 4)`). DynamoDB does not accept float types; it requires numeric values to be `int` or `Decimal`.

- First publish: no existing stories → `similar` list is empty → no score values → succeeds
- Second publish: one existing story → `similar` list contains `{"slug": "...", "score": 0.9}` where `0.9` is a `float` → DynamoDB rejects with `TypeError: Float types are not supported. Use Decimal types instead.` → 500 error

## Fix

Changed `src/app.py`:

1. Added import: `from decimal import Decimal`
2. Changed the return statement in `similarity()` from:
   ```python
   return round(0.7 * tag_score + 0.3 * word_score, 4)
   ```
   to:
   ```python
   return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
   ```

This ensures the score is stored as a `Decimal` type, which DynamoDB accepts. The `str()` conversion avoids floating-point precision issues when creating the Decimal.
