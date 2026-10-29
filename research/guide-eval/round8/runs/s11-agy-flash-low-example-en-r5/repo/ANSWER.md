# Post-Incident Analysis: Publish 500 on Second Write

## Cause

When the first story is published to an empty DynamoDB table, `table.scan()` returns no items. Because `existing` is empty, `related(story, existing)` returns an empty list `[]`. Consequently, the DynamoDB item stored has `"similar": []`, which contains no numerical scores.

When the second story is published:
1. `table.scan()` returns the first story.
2. `related(story, existing)` calls `similarity(story, other)`.
3. `similarity` computed a similarity score using floating-point arithmetic: `round(0.7 * tag_score + 0.3 * word_score, 4)`, returning a standard Python `float`.
4. This float was populated into `item["similar"]` as `{"slug": other["slug"], "score": <float>}`.
5. In DynamoDB (via boto3), Python `float` types are unsupported and rejected by `boto3.dynamodb.types.TypeSerializer._get_dynamodb_type` with:
   `TypeError: Float types are not supported. Use Decimal types instead.`
6. The unhandled exception caused `handler()` in `src/app.py` to catch `Exception` and return HTTP 500 (`Internal Server Error`).

## Fix

1. **Source Code (`src/app.py`)**:
   - Imported `Decimal` from the Python standard library `decimal` module.
   - Converted the computed float score in `similarity()` to `Decimal(str(score))`. DynamoDB natively serializes `Decimal` numbers without float precision issues.

2. **Integration Test (`tests/test_publish.py`)**:
   - Added `test_second_publish_with_similarity_scores` which seeds the DynamoDB table with a story and publishes subsequent stories (both via `publish()` and via `handler()`).
   - This ensures that code paths dependent on existing records (computing similarity scores and validating items containing scores against DynamoDB's type serializer) are executed and prevented from regressing.

## Colleague's Note: What Applied and What Was Ignored

### What Applied:
- **Core root cause analysis**: The observation that DynamoDB does not accept Python `float` values, and that the first publish succeeded only because an empty table bypassed the similarity scoring path entirely.
- **Data type fix**: Converting computed float scores to `decimal.Decimal` so DynamoDB's serializer accepts the item.
- **Testing recommendation**: Adding a seeded test case that writes a second item to exercise state-dependent code paths (similarity computation and storage) so regressions are caught.

### What Was Ignored:
- **Integer percentage conversion**: The colleague mentioned converting scores to integer percentages. In this service, similarity scores are represented with up to four decimal places of precision, so `Decimal(str(score))` was used instead of integer truncation or percentage conversion.
- **Deploy / Publish / External steps**: Any suggestions involving real AWS infrastructure or external deployments were ignored per ground rules (all verification was performed locally with the existing test harness).
