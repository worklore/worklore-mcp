# Second publish returns 500

## Cause

`similarity()` returns a Python `float` (`round(..., 4)`). `related()` put that
float straight into each `similar` entry, and `publish()` stored it in the
DynamoDB item.

boto3's DynamoDB serializer rejects floats:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The first publish worked because the library was empty, so `related()` returned
no entries and no float was ever written. The second publish is the first one
that has an existing story to compare against, so it writes a score and fails.
`handler()` catches the exception and returns 500. `logs/error.log` shows
exactly this: the 09:14 publish has `similar=0` and returns 201, and both 09:21
and 09:22 fail on `put_item` with the same TypeError.

I reproduced it locally with `tests/fake_dynamo.py`: the first handler call
returns 201, the second returns 500 with the same message.

## Fix

In `src/app.py`, `related()` now stores each score as a `Decimal`:

```python
scored.append({"slug": other["slug"], "score": Decimal(str(similarity(story, other)))})
```

`Decimal(str(...))` keeps the four-digit value exact, so `0.53` is stored as
`Decimal('0.53')`. `similarity()` still returns a float, which is fine for sorting
and is never written to DynamoDB.

## Preventing a regression

`tests/test_publish.py` has a new test,
`test_second_publish_with_related_stories_is_stored`. It publishes two stories
through `handler()`, expects 201 for the second, and checks that the stored
`similar` score is a `Decimal`. `FakeTable` already applies boto3's type rules,
so any future float in the item fails this test.

Against the original `app.py` the new test fails; with the fix, both tests pass:

```
python3 -m unittest discover tests
Ran 2 tests ... OK
```

Nothing was deployed, published, or sent anywhere external. The changes are
uncommitted in the working tree.
