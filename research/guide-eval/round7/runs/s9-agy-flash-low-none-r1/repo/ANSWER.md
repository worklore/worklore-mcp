# Root Causes for Story Library Issues

## 1. Production Crash on Hide (`logs/prod-error.log`)
- **Cause:** In DynamoDB, `HIDDEN` is a reserved keyword. In `StoryLibrary.hide()`, the update query used `UpdateExpression="SET hidden = :h, hidden_by = :by, hidden_at = :t"`. When a bare reserved keyword is used in an `UpdateExpression`, DynamoDB throws a `ValidationException: Attribute name is a reserved keyword; reserved keyword: hidden`.
- **Fix:** Used an Expression Attribute Name placeholder (`#hidden`) in the `UpdateExpression` and provided `ExpressionAttributeNames={"#hidden": "hidden"}` in the `update_item` call.

## 2. Manually Hidden Story Still Showing in Feed on Staging (`logs/bug-report.md`)
- **Cause:** In DynamoDB `ProjectionExpression`s, if a bare reserved keyword (such as `hidden`) is included, DynamoDB does not raise an exception; instead, it silently drops the attribute from the projected item returned in the response. Consequently, in `StoryLibrary.feed()`, `self.table.scan(ProjectionExpression="slug, title, hidden, published_at")` returned items without the `hidden` attribute. The feed filter `[i for i in resp["Items"] if not i.get("hidden")]` evaluated `i.get("hidden")` to `None`, thereby treating all hidden stories as unhidden and including them in the public feed.
- **Fix:** Aliased `#hidden` in `ProjectionExpression` using `ExpressionAttributeNames={"#hidden": "hidden"}` so DynamoDB properly projects and returns the `hidden` attribute in `scan`.

*(Note: `StoryLibrary.archive()` was also hardened to alias `#status` in its `ConditionExpression`, as `STATUS` is likewise a DynamoDB reserved keyword).*
