# Why Publishing Failed on the Second Request and How It Was Fixed

## Root Cause

1. **Empty Table on First Publish**:
   When the first story is published, the DynamoDB table is empty. In `src/app.py`, `table.scan()` returns no items, so `related(story, existing)` yields an empty list `similar: []`. All fields stored in DynamoDB (`slug`, `title`, `tags`, `body`, `published_at`, `similar`) are strings, integers, or lists thereof, which are natively supported by boto3's DynamoDB serializer. The first write succeeds with HTTP 201.

2. **Float Serialisation Failure on Subsequent Publishes**:
   When a second story is published, `table.scan()` returns the existing story. `related()` invokes `similarity()`, which calculates a score using Python `float` arithmetic:
   ```python
   return round(0.7 * tag_score + 0.3 * word_score, 4)
   ```
   This float is placed into `similar: [{"slug": ..., "score": <float>}]`. When `table.put_item(Item=item)` is executed, boto3's DynamoDB `TypeSerializer` encounters the `float` type and throws:
   ```text
   TypeError: Float types are not supported. Use Decimal types instead.
   ```
   The `handler()` catches the unhandled exception in `except Exception:`, logs `publish failed`, and responds with HTTP 500.

3. **Why It Slipped Past Tests**:
   The existing unit test only exercised the initial write against an empty table, leaving the non-empty `similar` scoring path completely untested.

---

## Fix

1. **Convert Similarity Scores to `Decimal` in `src/app.py`**:
   Imported `Decimal` from the `decimal` module and wrapped the similarity calculation with `Decimal(str(...))` so DynamoDB stores the score as a native numeric (`N`) attribute:
   ```python
   from decimal import Decimal

   def similarity(a, b):
       """Shared-tag ratio (Jaccard), blended with shared words of the two bodies."""
       ta, tb = set(a.get("tags", [])), set(b.get("tags", []))
       tag_score = len(ta & tb) / len(ta | tb) if (ta | tb) else 0
       wa, wb = words(a.get("body")), words(b.get("body"))
       word_score = len(wa & wb) / len(wa | wb) if (wa | wb) else 0
       return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
   ```

2. **Prevent Regression with Tests in `tests/test_publish.py`**:
   Added tests exercising the populated-table path:
   - `test_second_publish_computes_similar_with_decimal_score`: Verifies that publishing when records already exist populates `similar` with valid `Decimal` scores and succeeds in `table.put_item()`.
   - `test_handler_sequential_publishes_return_201`: Simulates multiple sequential publish requests via `handler()` to ensure subsequent publishes return HTTP 201 instead of 500.
