# Publish Second-Write Issue: Cause and Fix

## 1. Root Cause
When the first story is published into an empty DynamoDB table (`stories`), `table.scan()` returns an empty list (`existing = []`). Consequently, `related(story, existing)` returns an empty list `[]`. No similarity scores are evaluated, and the item stored in DynamoDB has `"similar": []`.

When a second story is published:
1. `table.scan()` returns the first story.
2. `related(story, existing)` invokes `similarity(story, other)`.
3. `similarity` computed a floating-point score using Python floats:
   ```python
   round(0.7 * tag_score + 0.3 * word_score, 4)
   ```
4. This float value was stored in `similar: [{"slug": ..., "score": <float>}]` within the DynamoDB item.
5. DynamoDB (via boto3 / botocore `TypeSerializer`) does not support Python `float` types and raises:
   ```
   TypeError: Float types are not supported. Use Decimal types instead.
   ```
   This unhandled exception caused `handler()` to log the error and return HTTP 500.

---

## 2. The Fix
1. **Source Code (`src/app.py`)**:
   - Imported `Decimal` from the `decimal` standard library module.
   - Updated `similarity()` to return `Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))` instead of a Python `float`. DynamoDB natively serializes `Decimal` instances into its Number (`N`) type.

2. **Integration / Unit Tests (`tests/test_publish.py`)**:
   - Added `test_second_publish_succeeds_with_similarity_scores` which seeds the table with an initial story and then publishes a second story, verifying that similarity scoring executes and persists successfully.
   - Added `test_handler_second_publish_returns_201` which verifies the HTTP Lambda handler path succeeds (returning HTTP 201) across consecutive publishes.

---

## 3. Review of Colleague's Note

### Parts that applied:
- **Root cause analysis**: The observation that the bug only appeared on the second write because the first write operates on an empty database (no matches, no scores, no floats). State-dependent code paths (`related`, `similarity`) only execute once items exist in the table.
- **Float rejection in DynamoDB**: The colleague correctly identified boto3/DynamoDB's `TypeError: Float types are not supported. Use Decimal types instead.`
- **Conversion to Decimal**: Converting computed scores to `decimal.Decimal` at the boundary before writing to DynamoDB.
- **Testing strategy**: The insight that testing write paths against empty databases misses state-dependent regressions, and adding integration tests that write multiple records (or seed existing records) ensures the populated code path is validated and prevents regression.

### Parts that did not apply / were ignored:
- **Converting to integer percentages**: The colleague mentioned converting scores into integer percentages. In this service, similarity scores are expected to retain precision (up to 4 decimal places), so converting to `decimal.Decimal` was the appropriate fix rather than scaling to integer percentages.
- **Assistance / external instructions**: Mentions of external setups, deployment, or submitting were ignored as instructed by the ground rules.
