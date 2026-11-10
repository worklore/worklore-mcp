## Cause

The `similarity()` function returns a Python `float` (via `round(..., 4)`). When a second story is published, `related()` computes similarity scores against the first story and stores them in the `similar` list as floats. DynamoDB via boto3 rejects float values with:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The first publish succeeds because there are no existing stories, so `similar` is an empty list `[]`. The second publish fails because it tries to store float scores for the first story.

## Fix

Changed `similarity()` to return `Decimal` instead of `float`:

```python
from decimal import Decimal

def similarity(a, b):
    ...
    return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
```

This ensures all numeric scores stored in DynamoDB are Decimal types, which boto3 accepts.
