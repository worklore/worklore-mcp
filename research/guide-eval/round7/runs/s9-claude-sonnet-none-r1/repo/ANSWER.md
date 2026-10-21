# Causes

Both reports come from the same thing: `hidden` is a DynamoDB **reserved word**, and `src/app.py` used it unescaped.

1. **Prod 500 on hide.** `hide()` wrote `SET hidden = :h, ...`. DynamoDB rejects a bare reserved word in an UpdateExpression with a `ValidationException`, so every hide call failed. Fix: `#hidden` with `ExpressionAttributeNames`.

2. **Staging: hidden story still in the feed.** Dasha's manual write was correct (`hidden: true` was stored). The bug is in the read side. `feed()` used `ProjectionExpression="slug, title, hidden, published_at"`. In a projection, a bare reserved word doesn't raise. The attribute is silently left out of the result. So `i.get("hidden")` was always `None`, the filter kept everything, and the feed returned 200 with no error. It wasn't a cache or a different table. Fix: project `#hidden` through `ExpressionAttributeNames`.

# Related fixes

- `archive()` had the same problem with `status` (reserved) in its ConditionExpression. It would have failed as soon as it was wired up. It now uses `#status`.
- `feed()` now follows `LastEvaluatedKey`, because a scan returns at most 1 MB per page.

# Keeping it from coming back

Added tests for hide, for a hand-hidden story (alias write), for hide on an unknown slug, and for archive. Added a guard test that records every expression the library sends and fails if any contains a bare reserved word.

Note that the fake's `RESERVED` list is only a subset of DynamoDB's roughly 570 reserved words. When you add a new attribute name, alias it with `#name` by default.
