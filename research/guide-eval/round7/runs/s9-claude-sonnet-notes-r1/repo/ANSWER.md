# Causes

Both bugs have one root cause: `hidden` is a DynamoDB reserved word, and `src/app.py` used attribute names bare in expressions.

1. **Prod crash on hide** – `hide()` used `SET hidden = :h ...` in its UpdateExpression. DynamoDB rejects a bare reserved word with `ValidationException: Attribute name is a reserved keyword: hidden`, so the handler returned a 500.
2. **Hidden story still in the feed (staging)** – `feed()` had `hidden` bare in its scan `ProjectionExpression`. A reserved word there raises no error. The field just comes back missing, so `not i.get("hidden")` was always true and nothing was filtered. Dasha's CLI write was correct (it used `#h`); the item really had `hidden: true`, but the feed never read it. No cache or second table was involved.

# Fix

- Every attribute name in every expression (update, condition, projection, including `publish`, `rename`, `archive`) now goes through `ExpressionAttributeNames` aliases. A future reserved field name can't break these calls.
- Tests added: hide removes the story from the feed, a story hidden out of band is excluded from the feed, and archive works (`status` is also a reserved word). The fake table follows DynamoDB's reserved-word rules, so the tests fail on the old code.

Nothing was deployed.
