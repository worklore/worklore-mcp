# Publishing Error Cause and Resolution

## Cause of the Bug
When publishing a story via `POST /stories`, the service calculates similarity scores between the incoming story and existing stories in the DynamoDB table (`src/app.py`: `similarity()`) to populate the `similar` field.

- On the **first publish**, the DynamoDB table is empty (`existing = []`). No similarity calculations are performed, so `similar` is an empty list `[]`. The story is written successfully.
- On the **second publish**, existing items are found in the table. The `similarity(a, b)` function calculates similarity as a weighted sum of Jaccard tag and body word overlap, returning a Python `float` via `round(0.7 * tag_score + 0.3 * word_score, 4)`.
- When `table.put_item(Item=item)` is called, `boto3` validates item types and rejects Python `float` types with:
  `TypeError: Float types are not supported. Use Decimal types instead.`
  This unhandled exception is caught by the Lambda `handler`, logged to `logs/error.log`, and returned as an HTTP 500 Internal Server Error.

## The Fix
1. **Application Code (`src/app.py`)**:
   - Imported `Decimal` from the `decimal` module.
   - Updated `similarity(a, b)` to convert the float score to `Decimal(str(round(...)))`. DynamoDB natively serializes `Decimal` values into its numeric attribute type `N`.

2. **Integration / Unit Tests (`tests/test_publish.py`)**:
   - Added `test_second_publish_with_similarity` to seed an initial record and execute a second publish, ensuring state-dependent code paths (similarity scoring and DynamoDB write serialization) are always exercised in tests to prevent regressions.

## Colleague's Note: What Applied and What Was Ignored

### What Applied:
- **Root Cause Analysis**: DynamoDB's rejection of Python float types (`TypeError: Float types are not supported. Use Decimal types instead.`) when state-dependent fields (`similar` scores calculated against existing items) are populated on the second write.
- **Empty-state vs. Populated-state Testing Gap**: The initial unit test only tested the empty-database path.
- **Conversion Boundary**: Converting computed floating-point values into DynamoDB-compatible numeric types (`Decimal`).
- **Seeded-Table Test Recommendation**: Adding a test that seeds a story and publishes a second story to exercise the populated path and prevent regressions.

### What Was Ignored:
- **Converting to Integer Percentages**: The note mentioned converting scores to integer percentages as an alternative option, but `Decimal` was used instead to preserve 4 decimal places of score precision expected by the similarity design.
- **Mentions of AWS Lambda runtime / external AWS environment**: Fix was made and verified locally with unit tests and fake DynamoDB without external deployments.
