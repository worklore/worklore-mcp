# Causes

Both symptoms come from one mistake: `hidden` is a DynamoDB reserved word, and `src/app.py` used it as a bare attribute name.

1. **Prod crash (`logs/prod-error.log`).** `hide()` used `SET hidden = :h, ...` in its `UpdateExpression`. DynamoDB rejects a bare reserved word there with `ValidationException: ... reserved keyword: hidden`, so the Hide button returned a 500.
2. **Staging story still in the feed (`logs/bug-report.md`).** The report's CLI command wrote `hidden: true` correctly, because it used the alias `#h`. The bug was in the read path. `feed()` scanned with `ProjectionExpression="slug, title, hidden, published_at"`. The colleague's note says a bare reserved word there returns the field absent instead of raising, and the repo's fake DynamoDB models that. So `i.get("hidden")` was always `None`, `not None` was true, and nothing was ever filtered out. There was no error and no log line, and the feed answered 200. It isn't a cache or a different table.

# Fix

Every attribute name in every expression in `src/app.py` now goes through an `#alias` and `ExpressionAttributeNames`. That covers `publish`, `rename`, `hide`, `feed` and `archive`. Names that are safe today are aliased too. `archive()` already had a latent bug of the same kind, because `status` is reserved, so it would have crashed on first use.

# Keeping it from coming back

I added three tests to `tests/test_feed.py`:
- Hiding through `hide()` removes the story from the feed.
- A story hidden by hand with the aliased CLI-style update is also excluded from the feed.
- `archive()` works.

All three write records with the field actually set. The two hide tests would have caught the silent feed bug, and the archive test would have caught the `status` crash. All 8 tests pass with the fix. Against the old `src/app.py`, 3 of them fail (1 failure, 2 errors).

Convention: alias every attribute name, always, and test each filtered field with data where the field is set.

# Colleague's note

- **Applied:**
  - The diagnosis, which matched both logs exactly.
  - The blanket-alias convention.
  - The advice to test with the field set.
- **Not applicable:**
  - The `similar` field, which this code doesn't have.
  - The "reproduce" steps against a real service. I didn't run anything against real AWS and used only the local fake.
