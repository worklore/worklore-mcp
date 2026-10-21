# Root Causes and Fixes

## 1. Production Crash on Hiding a Story (`logs/prod-error.log`)

### Cause
In `StoryLibrary.hide`, the `UpdateItem` call used the raw attribute name `hidden` in `UpdateExpression`:
```python
UpdateExpression="SET hidden = :h, hidden_by = :by, hidden_at = :t"
```
In DynamoDB, `hidden` is a reserved keyword. When an unescaped/bare reserved keyword is used in an `UpdateExpression` (or `ConditionExpression`), DynamoDB rejects the request with a `ValidationException`:
```
Invalid UpdateExpression: Attribute name is a reserved keyword; reserved keyword: hidden
```

## 2. Manually Hidden Story Still Showing in Public Feed on Staging (`logs/bug-report.md`)

### Cause
In `StoryLibrary.feed`, the `scan` call used `hidden` directly in `ProjectionExpression`:
```python
resp = self.table.scan(ProjectionExpression="slug, title, hidden, published_at")
```
In DynamoDB, when a reserved keyword is used bare in a `ProjectionExpression`, DynamoDB does not raise an exception. Instead, it silently drops the reserved attribute from the projected attributes in the response items.

Because `hidden` was silently omitted from every item returned by the scan, `item.get("hidden")` evaluated to `None` for all records—even those where `hidden` was set to `true` in the table (such as via manual CLI update). Thus, `not i.get("hidden")` was always `True`, causing hidden stories to remain visible in the feed.

## 3. Resolution and Prevention

1. **ExpressionAttributeNames Aliasing**:
   Updated all DynamoDB operations across `src/app.py` (`publish`, `rename`, `hide`, `feed`, and `archive`) to alias every attribute name in `UpdateExpression`, `ConditionExpression`, and `ProjectionExpression` using `ExpressionAttributeNames` (e.g., `#h` for `hidden`, `#s` for `slug`, `#t` for `title`, `#p` for `published_at`, `#st` for `status`, etc.). This eliminates conflicts with DynamoDB reserved keywords.

2. **Automated Regression Tests**:
   Added unit tests in `tests/test_feed.py` covering:
   - Calling `hide()` and verifying that the story is excluded from `feed()`.
   - Manually setting `hidden = True` on an item in DynamoDB and verifying that `feed()` excludes it (verifying that projection expressions properly include the attribute).
   - Calling `archive()` to ensure aliasing works across other expressions.
