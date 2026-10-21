# Root Causes and Fixes

## 1. Why hiding a story crashes on prod (`logs/prod-error.log`)

In `StoryLibrary.hide` ([src/app.py](file:///tmp/h-Gyfxdp/src/app.py)), the call to `update_item` used:
```python
UpdateExpression="SET hidden = :h, hidden_by = :by, hidden_at = :t"
```
In DynamoDB, `hidden` is a reserved keyword. Using bare reserved words in an `UpdateExpression` triggers a `ValidationException` (`Attribute name is a reserved keyword; reserved keyword: hidden`), crashing the API call with a 500 status code.

## 2. Why a manually hidden story still shows in the public feed on staging (`logs/bug-report.md`)

In `StoryLibrary.feed` ([src/app.py](file:///tmp/h-Gyfxdp/src/app.py)), the scan operation fetched items using:
```python
ProjectionExpression="slug, title, hidden, published_at"
```
When a reserved keyword like `hidden` is used bare in a `ProjectionExpression`, DynamoDB does not raise an error; instead, it silently drops the attribute from the projected item. Because `hidden` was omitted from the returned dictionary, the Python filter:
```python
items = [i for i in resp["Items"] if not i.get("hidden")]
```
evaluated `i.get("hidden")` as `None`, so `not i.get("hidden")` evaluated to `True`. Thus, hidden stories were never filtered out and continued appearing in the feed.

## 3. The Fix

To ensure these issues cannot recur:
- Aliased all attribute names in DynamoDB expressions (`UpdateExpression`, `ProjectionExpression`, and `ConditionExpression`) across [src/app.py](file:///tmp/h-Gyfxdp/src/app.py) using `#alias` placeholders mapped in `ExpressionAttributeNames` (e.g., `#hidden`, `#slug`, `#title`, `#published_at`, `#status`, `#archived_at`, etc.).
- Added unit tests in [tests/test_feed.py](file:///tmp/h-Gyfxdp/tests/test_feed.py) covering `hide` and verifying that hidden items are properly excluded from `feed()`.

---

## Colleague's Note: What Applied and What Was Ignored

### What applied:
- **Reserved keyword crash on `UpdateExpression`**: The explanation that `hidden` is a DynamoDB reserved keyword that raises a `ValidationException` when used bare in an `UpdateExpression` directly applied to the prod crash.
- **Silent omission in `ProjectionExpression`**: The explanation that bare reserved keywords in `ProjectionExpression` do not throw an error but cause DynamoDB to silently omit the field (causing `not item.get("hidden")` to fail to filter anything) directly explained the staging bug report.
- **Blanket aliasing convention**: The recommendation to alias every attribute name across all DynamoDB expressions (`UpdateExpression`, `ProjectionExpression`, `ConditionExpression`) using `#alias` and `ExpressionAttributeNames` rather than maintaining an ad-hoc per-word whitelist was implemented across [src/app.py](file:///tmp/h-Gyfxdp/src/app.py).
- **Testing with populated fields**: The recommendation to add tests asserting that records with the field set actually get excluded by the filter was applied in [tests/test_feed.py](file:///tmp/h-Gyfxdp/tests/test_feed.py).

### What was ignored:
- **`similar` keyword and other specific field references**: References to `similar` lists, author-withdraws-story specific anecdotes, and unrelated field names mentioned in the colleague's debugging timeline.
- **Reproduce instructions referring to CLI / AWS credentials / deployment**: The reproduction steps mentioned running against external services or deploying; per project guidelines, no external deployments or service interactions were run, and verification was performed within the repo using [tests/fake_dynamo.py](file:///tmp/h-Gyfxdp/tests/fake_dynamo.py) and unittest.
