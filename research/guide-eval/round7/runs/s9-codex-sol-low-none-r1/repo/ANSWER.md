# Causes and fix

- **Hide crashes:** `hide()` used the reserved DynamoDB word `hidden` directly in its `UpdateExpression`. DynamoDB rejected the update with `ValidationException`, which surfaced as a 500. The update now uses `#hidden` with `ExpressionAttributeNames`.
- **Hidden story stays in the feed:** `feed()` also used `hidden` directly in its `ProjectionExpression`. The projection omitted that attribute, so `i.get("hidden")` was false even for a hidden story. This was a read bug in the same table, not a cache issue. The projection now aliases `hidden`, allowing the existing filter to exclude it.

Regression tests cover hiding through `StoryLibrary.hide()` and reading a story whose `hidden` field was set directly. `python3 -m unittest discover tests` passes (7 tests).
