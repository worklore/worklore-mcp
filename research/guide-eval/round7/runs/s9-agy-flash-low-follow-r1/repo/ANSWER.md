# Root Causes and Solutions

## 1. Production Crash (`logs/prod-error.log`)
- **Cause**: DynamoDB maintains a reserved words list containing `hidden` (among ~573 reserved words). In `StoryLibrary.hide()`, the `UpdateExpression` used the bare attribute name `hidden` (`SET hidden = :h, hidden_by = :by, hidden_at = :t`). When DynamoDB evaluates an `UpdateExpression` with a bare reserved keyword, it raises a `ValidationException: Attribute name is a reserved keyword; reserved keyword: hidden`, leading to unhandled 500 exceptions on production.
- **Fix**: Aliased all attribute names in the `UpdateExpression` and `ConditionExpression` via `#alias` tokens mapped in `ExpressionAttributeNames` (`#hidden`, `#hidden_by`, `#hidden_at`, `#slug`).

## 2. Hidden Story Showing in Public Feed on Staging (`logs/bug-report.md`)
- **Cause**: In `StoryLibrary.feed()`, the DynamoDB `scan` operation used a bare attribute name in `ProjectionExpression="slug, title, hidden, published_at"`. In DynamoDB, bare reserved words like `hidden` in a `ProjectionExpression` do not throw an error or log a warning; instead, DynamoDB silently drops/omits the reserved attribute from the projected item response. As a result, `i.get("hidden")` returned `None` during post-scan Python filtering (`if not i.get("hidden")`), causing manually or successfully hidden items to never match the exclusion filter and remain in the public feed.
- **Fix**: Replaced bare attribute names in the `ProjectionExpression` with `#alias` placeholders (`#slug, #title, #hidden, #published_at`) and defined them in `ExpressionAttributeNames`.

## Blanket Prevention
- Adopted the convention across all DynamoDB expressions (`publish`, `rename`, `hide`, `feed`, and `archive`) to alias every attribute name in `UpdateExpression`, `ProjectionExpression`, and `ConditionExpression` using `ExpressionAttributeNames`.
- Added unit/integration tests in `tests/test_feed.py` verifying that:
  - Calling `hide()` removes withdrawn stories from the feed.
  - Stories with `hidden: True` set directly in DynamoDB are excluded from the public feed.
