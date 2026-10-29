# Second publish returns 500: float in DynamoDB item

## Cause

`publish()` stores each story with `similar`: the top three existing stories by
similarity. `related()` builds that list from `similarity()`, which returns
`round(..., 4)`, a Python `float`.

- **First publish:** the table is empty, so `related()` never calls
  `similarity()`. `similar` is `[]`, there are no floats, and the write succeeds.
- **Second publish:** there is one story to compare against, so `similar`
  contains `{"slug": ..., "score": 0.1234}`. boto3 rejects the float with
  `TypeError: Float types are not supported. Use Decimal types instead.`
  `handler()` catches it and returns 500.

The bug depends on stored data. Any publish after the first one that finds a
related story fails, so it cannot be fixed by retrying.

`logs/error.log` matches this: the 09:14 publish has `similar=0` and returns 201;
the 09:21 and 09:22 publishes fail in `table.put_item` with the float TypeError.

## Fix

`src/app.py`, in `related()`: the score is converted to `Decimal` at the write
boundary.

```python
scored.append({"slug": other["slug"], "score": Decimal(str(similarity(story, other)))})
```

`Decimal(str(x))` keeps the 4-decimal value exact, where `Decimal(x)` would store
the float's binary expansion. Sorting still works because `Decimal` compares with
`Decimal`. The scoring math is unchanged.

I checked the rest of `app.py` with a grep for `round(`, `/`, and `float(`. The
only other float-producing lines are the divisions in `similarity()` (lines 28
and 30), which are intermediates and never reach an item. `published_at` is an
`int`. No other float reaches a DynamoDB write.

## Keeping it from coming back

`tests/test_publish.py` gets `test_second_publish_with_related_stories_is_stored`.
It seeds one story, then calls `handler()` for a second one, the same path
production uses, and asserts a 201, that the related slug is stored, and that
the score is a `Decimal`.

The test fails without the fix: running it against the old `src/app.py` gives a
failure on the 500 status. With the fix, both tests pass:

```
python3 -m unittest discover tests
OK
```

The existing fake table in `tests/fake_dynamo.py` already rejects floats the way
boto3 does, so any future float in an item will fail the tests.

## Colleague's note: what applied

- **Applied:** the diagnosis. The first write hid the bug because the code path
  depends on existing state. The fix is to convert at the DynamoDB boundary.
- **Applied:** the seeded-table test. The new test seeds a record and writes a
  second one, so the populated path runs under test.
- **Applied:** the grep for `round(` and `/` feeding item dicts. I did it by hand
  with grep, as the note describes.
- **Not applied:** integer percentages. That would change the stored score
  format, and nothing in the repo says the reader expects percentages. `Decimal`
  keeps the existing values.
- **Not done:** publishing twice against a real table. The ground rules forbid
  deploying or publishing to external services, so the fix is verified only with
  the in-memory table. Before relying on it in production, run the second publish
  against the real `stories` table in a non-production environment.

## Not committed

The changes are uncommitted: `src/app.py`, `tests/test_publish.py`, and this file.
