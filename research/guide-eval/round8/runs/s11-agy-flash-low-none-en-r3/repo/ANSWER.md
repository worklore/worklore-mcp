# Root Cause and Fix

## Root Cause
When the first story is published to an empty DynamoDB table, `table.scan()` returns no existing items (`existing = []`). Consequently, `related(story, existing)` returns an empty list (`similar: []`), and the item is stored successfully without calculating any similarity scores.

When a second story is published, existing stories exist in the table. `publish()` calls `related(story, existing)`, which invokes `similarity(a, b)`. `similarity()` computed the similarity score as a Python `float` using `round(0.7 * tag_score + 0.3 * word_score, 4)`.

DynamoDB (and boto3's `TypeSerializer`) does not support Python `float` types and strictly requires `Decimal` for floating-point numbers:
`TypeError: Float types are not supported. Use Decimal types instead.`

This caused `table.put_item(Item=item)` to raise a `TypeError`, which was caught by the general `except Exception:` block in `handler()` and returned a `500 Internal Server Error`.

## Fix
1. In `src/app.py`:
   - Imported `Decimal` from standard library `decimal`.
   - Updated `similarity(a, b)` to return a `Decimal` representation of the rounded score (`Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))`).
2. In `tests/test_publish.py`:
   - Added a regression unit test `test_publish_multiple_stories_with_similarity` that publishes consecutive stories, triggering the similarity calculation and verifying that the `similar` list contains items with `Decimal` scores and succeeds with HTTP 201.
