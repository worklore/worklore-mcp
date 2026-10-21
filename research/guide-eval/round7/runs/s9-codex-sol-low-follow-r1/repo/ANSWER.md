# Causes and fix

- **Production hide crash:** `StoryLibrary.hide()` put the reserved DynamoDB attribute name `hidden` directly in its `UpdateExpression`. DynamoDB rejected the update with the `ValidationException` shown in `logs/prod-error.log`, so the Hide request returned 500.
- **Staging feed leak:** The story was successfully marked `hidden: true` by the CLI, but `StoryLibrary.feed()` used bare `hidden` in its `ProjectionExpression`. In this service's read path, the projected item then lacked `hidden`; `not item.get("hidden")` evaluated to true and included the story. The bug report's successful `get-item` and persistent feed result match this path; caching or a different table is not needed to explain it.
- **Underlying issue:** DynamoDB expression attribute names were used bare throughout `src/app.py`. The unused `archive()` path also used reserved `status` in a condition and would fail when called.

Every attribute name in the library's DynamoDB expressions now uses an `#alias` with `ExpressionAttributeNames`. Regression tests cover both hiding through the library and a story marked hidden directly in the table, then assert the public feed excludes it. A test also exercises the reserved `status` condition in `archive()`.
