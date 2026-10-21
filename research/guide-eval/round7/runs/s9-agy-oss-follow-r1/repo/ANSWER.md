---
title: DynamoDB reserved words — the crash, and the silent filter that shipped nothing
date: 2026-08-04
tags: [dynamodb, aws, python, boto3, expressionattributenames, debugging]
type: success
reproducible: true
---

# Findings

## Root causes

1. **UpdateExpression uses a reserved word**
   - The `hide` method performed:
   ```python
   UpdateExpression="SET hidden = :h, hidden_by = :by, hidden_at = :t"
   ```
   - `hidden` is a DynamoDB reserved keyword. When the update is executed the service throws a `ValidationException` (see `logs/prod-error.log`).

2. **ProjectionExpression uses the same reserved word without alias**
   - The `feed` method scanned the table with:
   ```python
   ProjectionExpression="slug, title, hidden, published_at"
   ```
   - In a `ProjectionExpression` a reserved word does **not** raise an error; the attribute is silently omitted from the returned items. Consequently the `i.get("hidden")` filter never sees the flag, so hidden stories remain in the public feed (see `logs/bug-report.md`).

## Why the bug manifested differently
- The update path fails loudly, so the API returns a 500 and the write never succeeds.
- When the write succeeds (e.g., via the CLI with an explicit alias), the read path silently drops the `hidden` attribute, so the downstream filter never excludes the story.

## Fix applied
- **Always alias reserved attributes** in every DynamoDB expression.
  ```python
  # hide method
  UpdateExpression="SET #h = :h, hidden_by = :by, hidden_at = :t",
  ExpressionAttributeNames={"#h": "hidden"}
  ```
- **Alias the `hidden` field in the scan** as well:
  ```python
  resp = self.table.scan(
      ProjectionExpression="slug, title, #h, published_at",
      ExpressionAttributeNames={"#h": "hidden"})
  ```
- The feed logic continues to check `i.get("hidden")`; after the alias the attribute is present, and hidden stories are correctly excluded.

# Outcome
- The `hide` endpoint now succeeds (no 500s).
- The public feed no longer shows stories that have `hidden = true`.
- Tests continue to pass (`pytest -q` reports 5 passed).

---

*All DynamoDB attribute names should be aliased, even if they appear safe today, to guard against future additions to the reserved‑word list.*