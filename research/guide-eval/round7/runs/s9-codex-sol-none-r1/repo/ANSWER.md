# Causes and fixes

- **Production hide crash:** `hide()` used the reserved DynamoDB attribute name `hidden` directly in its `UpdateExpression`. DynamoDB rejected the update with the logged `ValidationException`. The update now uses an expression attribute name (`#hidden`).
- **Staging story still in feed:** `feed()` also used bare `hidden` in its `ProjectionExpression`. The table stand-in omits that reserved attribute from the projected rows, so `i.get("hidden")` was false even for the manually hidden story. The feed now projects `hidden` through `#hidden`, allowing the existing visibility check to exclude it.
- **Related archive path:** `archive()` used the reserved name `status` directly in its condition, and the feed did not check `archived_at`. The condition now aliases `status`, and archived stories are excluded from the public feed as its method contract requires.

Regression tests cover hiding through the library, a row hidden directly in the table, an absent slug, and archiving. Run them with `python3 -m unittest discover tests`.
