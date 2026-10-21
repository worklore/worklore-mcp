# Causes and fix

- **Production hide crash:** `StoryLibrary.hide()` used `hidden` as a bare attribute name in its DynamoDB `UpdateExpression`. `hidden` is reserved, so DynamoDB rejected the update with the `ValidationException` shown in `logs/prod-error.log`. The story was never hidden.
- **Staging story still in the feed:** The manual update did set `hidden: true`, but `StoryLibrary.feed()` also used bare `hidden` in its scan `ProjectionExpression`. In this read path, the reserved attribute was omitted from the returned items. The subsequent `not item.get("hidden")` check interpreted the missing flag as visible and included the story. The report's successful `get-item` and repeated feed results fit this path; no cache or different table is needed to explain them.

Every attribute name in the library's DynamoDB expressions now uses an `ExpressionAttributeNames` placeholder, including `hidden` in both paths and `status` in `archive()` (another reserved word). Regression tests cover hiding through the library, a story hidden directly in the table, and the archive condition. `python3 -m unittest discover tests -v` passes all 8 tests.
