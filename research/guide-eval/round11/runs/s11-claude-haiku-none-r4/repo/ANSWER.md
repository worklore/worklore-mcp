# Why the second publish returns 500

## Cause

`publish()` stores each story with `similar`: the three most similar existing
stories, each as `{slug, score}`. The score comes from `similarity()`, which
returns a Python `float` (`round(..., 4)`).

DynamoDB does not accept Python floats. boto3 serializes numbers only as
`Decimal` (or `int`), so `put_item` raises
`TypeError: Float types are not supported. Use Decimal types instead.`

The first publish has an empty library, so `similar` is `[]` and no float is
ever written. That is why it returned 201. The second publish finds one
existing story, builds `similar = [{"slug": ..., "score": 0.5}]`, and the float
inside it makes the write fail. `handler()` catches the exception and returns
500. The log matches: the `INFO ... stored` line for the first story, then the
`TypeError` on the next publish.

The bug was not caught by the existing test because it only publishes one
story, so `similar` is always empty and no score is ever written. The fake
table does reject floats, so the test just never reached that path.

## Fix

- `src/app.py`: `related()` now stores the score as `Decimal(str(score))`.
  Building it from the string form keeps the exact 4-digit value. Sorting still
  works because `Decimal` compares with `Decimal`.
- `tests/test_publish.py`: two regression tests:
  - `test_second_publish_stores_related_scores` publishes two stories and checks
    that the stored score is a `Decimal`.
  - `test_handler_second_publish_returns_201` checks the production path: the
    second `handler()` call returns 201 instead of 500.

Both tests fail on the original `src/app.py` and pass with the fix. The full
suite passes (`python3 -m unittest discover tests`).

## Keeping it from coming back

The regression tests cover the exact path that failed. The fake table in
`tests/fake_dynamo.py` already rejects floats the way DynamoDB does, so any
future float in an item will fail the tests before deploy.
