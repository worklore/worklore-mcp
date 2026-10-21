# Causes

1. **Prod crash on hide**: `StoryLibrary.hide` used `hidden` bare in `UpdateExpression`.
   `hidden` is a DynamoDB reserved word, so UpdateItem raised `ValidationException` (HTTP 500).
2. **Hidden story still in the feed (staging)**: `feed()` had `hidden` bare in the scan's
   `ProjectionExpression`. A reserved word there doesn't raise. The field just comes back
   missing, so `not i.get("hidden")` was always true and nothing was filtered. Dasha's hand-written
   CLI update used an alias and wrote `hidden: true` correctly. The bug was on the read side.
   It was not caching or a different table.
   (Also, the old tests never set `hidden`, so they couldn't catch it.)

# Fix

- Every attribute name in every expression in `src/app.py` is now aliased (`#hid`, `#ttl`, `#slug`, ...)
  through `ExpressionAttributeNames`. This is a blanket rule, not a per-word check.
  That includes `rename`, `publish` and `archive`. `archive` used bare `status`, another
  reserved word, and would have crashed as soon as it was wired up.
- New tests set the field: hide removes a story from the feed, a hand-set `hidden` is excluded,
  and `archive` works.

# Not changed, worth checking

`dynamo_table()` falls back to table `stories` if `STORIES_TABLE` is unset. Confirm staging sets it
to `stories-staging`. Otherwise the feed would read the wrong table.
