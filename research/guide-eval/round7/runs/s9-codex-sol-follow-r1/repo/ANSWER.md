# Causes and fix

1. **Production hide crash:** `StoryLibrary.hide()` used `hidden` directly in its DynamoDB `UpdateExpression`. `hidden` is reserved, so DynamoDB rejected the update with the `ValidationException` shown in `logs/prod-error.log`. The story was never hidden through that path.
2. **Staging feed leak:** The manual CLI update did store `hidden: true`, but `StoryLibrary.feed()` used bare `hidden` in its `ProjectionExpression`. In this read path the projected item lacked `hidden`, so `not item.get("hidden")` evaluated to true and included the story. This was a projection and filtering bug, not a cache issue. The existing feed tests only used stories without `hidden`, so they did not catch it.
3. **Same class of latent failure:** Other expressions used bare attribute names, including reserved `status` in `archive()`'s condition. A future call to that path would fail similarly.

All attribute names in this module's DynamoDB expressions now use `#` placeholders with `ExpressionAttributeNames`. Regression tests cover hiding through the library, a story whose `hidden` flag was set outside the library, and the archive condition. `python3 -m unittest discover -s tests -v` passes all eight tests.
