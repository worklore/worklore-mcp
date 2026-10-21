# Cause and Fix for Second Publish 500 Error

## Cause
On the first publish to an empty DynamoDB table (`stories`), `table.scan()` returns no items (`existing = []`). As a result, `related(story, existing)` returns an empty list (`similar: []`), and no similarity score is computed or stored.

On the second publish, the table contains existing stories, so `similarity(story, other)` is invoked. In Python, `similarity()` calculated a floating-point score:
```python
round(0.7 * tag_score + 0.3 * word_score, 4)
```
Boto3's DynamoDB serializer (`TypeSerializer`) does not support Python `float` values, raising:
```
TypeError: Float types are not supported. Use Decimal types instead.
```
This unhandled exception caused the Lambda `handler()` to catch the generic exception and return `500 Internal Server Error`.

## Fix
1. **Source Fix (`src/app.py`)**:
   Imported `Decimal` from Python's standard `decimal` library and converted the computed similarity score from `similarity()` to `Decimal`:
   ```python
   return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
   ```
   DynamoDB serializes `Decimal` numbers without error.

2. **Regression Prevention / Test Suite Update (`tests/test_publish.py`)**:
   Added an integration test (`test_second_publish_succeeds_with_similarity_scores`) that publishes an initial story and then performs a second publish. This exercises the non-empty table write path where similarity scoring executes, ensuring floats cannot be reintroduced into DynamoDB items.

## Colleague's Note: What Applied and What Was Ignored

### Parts that applied:
- **Root cause analysis**: The observation that DynamoDB rejects Python `float` values (`TypeError: Float types are not supported. Use Decimal types instead.`) and that the bug only surfaces when existing records exist because similarity calculation is bypassed on an empty table.
- **Conversion to Decimal**: Converting floating-point scores to `Decimal` before writing to DynamoDB.
- **Testing recommendations**: Seeding/testing against a populated table (publishing at least twice) to exercise state-dependent code paths.

### Parts ignored:
- Converting similarity scores to integer percentages: Retaining `Decimal(str(round(...)))` preserves the existing 4-decimal-place precision expected by clients without changing score representation to integer percentages.
- Advice regarding external deployment, publishing, or real AWS tables, as the workspace uses local tests (`FakeTable`) under the given ground rules.
