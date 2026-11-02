# Why the second publish returns 500

## Cause

`publish()` stores each story with its related stories, `similar: [{slug, score}]`.
`similarity()` returns a Python `float` (`round(0.7 * tag_score + 0.3 * word_score, 4)`),
and boto3's DynamoDB serializer rejects floats:

    TypeError: Float types are not supported. Use Decimal types instead.

(`logs/error.log`, from `table.put_item` at `src/app.py:63`.)

The first publish worked only because the library was empty: `similar` was `[]`
(`similar=0` in the log), so no float got into the item. From the second publish
on, there is at least one existing story to score, a float goes into the item,
`put_item` raises, and `handler` turns that into a 500. Every publish after the
first one fails this way.

The test suite didn't catch it because it only ever published one story into an
empty table, which is the one case where no score gets computed.

## Fix

- `src/app.py`: new `to_dynamo()` turns every float in a value into
  `Decimal(str(f))`, at any depth. `publish()` now runs the whole item through it
  right before `put_item`. Because the conversion happens at the storage boundary
  instead of on the `score` field alone, a float added to the item later (another
  score, a ratio, a weight) can't bring the bug back. Using `Decimal(str(f))`
  keeps the rounded value: `0.4667` is stored as `Decimal("0.4667")`, not as the
  binary float's long expansion.
- `tests/fake_dynamo.py`: `get_item`/`scan` now return every number as a
  `Decimal`, the way real boto3 reads them back. Before, the fake handed back plain
  ints and floats, so it was more forgiving than production.
- `tests/test_publish.py`: two new tests.
  - One publishes three stories through `handler` and checks each returns 201 and
    the related scores are stored.
  - One is a unit test of `to_dynamo` on nested floats.

## Verification

- `python3 -m unittest discover tests` → 3 tests, OK.
- With the `src/app.py` fix reverted (new tests kept), the multi-publish test fails
  with `500 != 201` and the same `TypeError: Float types are not supported` as in
  production. So the test catches this exact bug, not something nearby.

Nothing was deployed. Production starts accepting publishes again after the next
`sam deploy`.
