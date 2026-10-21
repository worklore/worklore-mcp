# Cause and Fix

## Cause of the 500 error on second publish

The Lambda handler stores a story together with a list of *related* stories. The `related` function originally returned a list of dictionaries where the `score` field was a **float** (e.g., `0.8234`).

DynamoDB (accessed via `boto3`) does **not** support native Python `float` types – it only accepts `Decimal` objects for number attributes. When the first story is published the `similar` list is empty, so DynamoDB does not see any float values and the request succeeds. On the second publish the list contains at least one related story, the `float` tries to be written, and `boto3` raises:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The exception bubbles up to the generic handler, which returns a **500 Internal Server Error**.

## Fix implemented

1. **Convert similarity scores to `Decimal`.**
   - Updated `src/app.py` – the `related` function now:
     - Imports `Decimal` from the standard library.
     - Converts the float produced by `similarity()` to `Decimal` using `Decimal(str(score))` (preserves the rounded four‑decimal representation).
     - Added a docstring explaining why the conversion is required.
2. The change is localized to the `related` function; no other parts of the code need modification because DynamoDB will now receive numbers in a supported type.

With this change the second publish succeeds, and the endpoint consistently returns **201** for valid stories.

---

*All work was performed inside the current workspace (`/tmp/h-1JQLbA`). No external services were invoked.*