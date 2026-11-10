# Cause and Fix for Second Publish 500 Error

## Cause

The `similarity()` function in `src/app.py` returns a Python `float` via `round(0.7 * tag_score + 0.3 * word_score, 4)`. When the DynamoDB table is empty, the first publish has no existing stories, so `related()` returns an empty list and no float scores are stored — the write succeeds. On the second publish, `related()` computes similarity scores (floats) between the new story and the existing one, and stores them in the `similar` field of the item. DynamoDB's boto3 serializer rejects float values with: `TypeError: Float types are not supported. Use Decimal types instead.`

## Fix

**src/app.py line 38**: Changed the score storage in `related()` from the raw float to an integer percentage:

```python
# Before:
scored.append({"slug": other["slug"], "score": similarity(story, other)})

# After:
scored.append({"slug": other["slug"], "score": int(similarity(story, other) * 100)})
```

This converts the float similarity score (e.g., 0.85) to an integer percentage (85), which DynamoDB accepts.

**tests/test_publish.py**: Added a second test `test_publish_with_existing_story_computes_similarity` that seeds the table with one story before publishing a second one. This exercises the state-dependent code path (similarity computation with existing data) that the original single-story test never touched.

## Which parts of the colleague's note applied

- **Applied**: The core diagnosis — DynamoDB rejecting Python floats, first write surviving because the table was empty, second write failing when similarity scores were computed and stored.
- **Applied**: The lesson about state-dependent code paths needing populated-table tests.
- **Applied**: The fix strategy of converting floats to integers at the DynamoDB boundary.
- **Not applied**: The colleague's specific context (AWS Lambda, their exact test setup) — we adapted the approach to our codebase.
