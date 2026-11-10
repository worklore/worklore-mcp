**Cause**

The `publish` handler builds a list of related stories by calling `related()`. The original implementation stored the raw similarity score as a Python `float`. When the DynamoDB table already contains a story, `related()` runs, the float is placed into the item, and DynamoDB (or the `FakeTable` used in tests) rejects it with:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

On the first publish the table is empty, so `related()` returns an empty list and no float is stored – the request succeeds. Subsequent publishes hit the failing path.

**Fix**

Convert the similarity score to an integer percentage (0‑100) before storing it. This keeps the ordering while using a DynamoDB‑compatible type (`int`).

Implemented in `src/app.py`:

```python
def related(story, existing):
    """Return top N related stories with integer percent scores.
    ...
    """
    scored = []
    for other in existing:
        if other["slug"] == story["slug"]:
            continue
        raw_score = similarity(story, other)
        int_score = int(round(raw_score * 100))
        scored.append({"slug": other["slug"], "score": int_score})
    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored[:TOP_N]
```

**What from the colleague's note applied**

- Observation that the bug appears only after the table has data (empty‑table path works).
- Root cause: storing Python floats in DynamoDB.
- Solution: convert scores to integer percentages.

All tests now pass (`pytest -q` reports 1 passed).
