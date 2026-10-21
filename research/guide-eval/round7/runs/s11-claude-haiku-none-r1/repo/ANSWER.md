# Second publish returns 500

## Cause

`related()` in `src/app.py` put each similarity score into the item as a
Python `float` (`similarity()` returns `round(..., 4)`, a float). The first
publish has no existing stories, so `similar` is empty and no float is ever
written. The second publish finds one existing story, so `similar` holds
`{"slug": ..., "score": 0.1667}`. boto3's DynamoDB serializer rejects floats:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

`handler()` catches the exception and returns 500. This matches
`logs/error.log`: the first publish (09:14) returns 201, and the publishes at
09:21 and 09:22 both fail in `table.put_item` with that error.

The existing test only publishes once, so the bug never ran in the suite.

## Fix

`src/app.py`, in `related()`: store the score as a `Decimal`, built from the
string form so the rounded value stays exact:

```python
score = Decimal(str(similarity(story, other)))
```

## Preventing a regression

`tests/test_publish.py` gains two tests:

- `test_second_publish_with_related_stories_is_stored` publishes two stories
  and checks that the second one is stored with one related entry.
- `test_handler_second_publish_returns_201` runs the same sequence through
  `handler()` and checks for 201 on both calls.

Both fail on the original `app.py` and pass with the fix. `FakeTable` already
rejects floats the way boto3 does, so the tests catch this class of error
without AWS.

Run: `python3 -m unittest discover tests` from the repo root.
