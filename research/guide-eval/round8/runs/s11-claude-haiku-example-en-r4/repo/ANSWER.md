# Second publish returns 500: float score written to DynamoDB

## Cause

`publish()` stores each story with `similar`, a list of `{slug, score}` for the
three most similar existing stories. `score` comes from `similarity()`, which
returns `round(..., 4)`. Python's `round()` on these Jaccard ratios returns a
`float`, and boto3's DynamoDB serializer rejects floats:

    TypeError: Float types are not supported. Use Decimal types instead.

(`logs/error.log`, `src/app.py:63`, the `put_item` call.)

Why the first publish worked: `table.scan()` returned nothing on the empty
table, so `related()` never called `similarity()` and `similar` was `[]`. No
float was built. The bug only exists once the table has at least one story.

Why the tests missed it: `tests/test_publish.py` only publishes into an empty
`FakeTable`, so it never reaches the score path. `FakeTable` already rejects
floats (`tests/fake_dynamo.py`), so the test would have caught this if it had
ever run the populated path.

## Fix

- `src/app.py`: `related()` now stores the score as `Decimal(str(...))`. The
  float stays inside `similarity()` and the sort, and is converted at the point
  it enters the item. `str()` keeps the 4-decimal value exact, so the stored
  number is `0.3333`, not `0.33329999...`.
- `tests/test_publish.py`: new test
  `test_second_publish_with_existing_story_stores_related`. It seeds one record
  with `put_item`, then publishes a second story and asserts that `similar`
  holds the seeded slug with a `Decimal` score. Against the old code it fails
  with the same TypeError as production (verified before the fix).

Result: `python3 -m unittest discover tests` passes both tests.

To keep it from coming back: the seeded test runs the populated path, so
`FakeTable`'s float check now fires on any float written in that path. Any
future computed value (averages, counters, new scores) must go through
`Decimal` or `int` before it reaches `put_item`.

## Which parts of the colleague's note applied

- **Applied:** the diagnosis (the bug sits on the populated path, the first
  write never exercises it); the seeded integration test; grepping for
  computed values that reach an item dict; converting at the boundary with
  `Decimal`.
- **Applied, with a note:** the grep. `round(` and `/` appear only in
  `similarity()` (`src/app.py:28-31`). The only route from them into an item is
  `related()` → `similar[].score`. `published_at` uses `int(time.time())`, which
  is already an int.
- **Not applied:** converting scores to integer percentages. That changes the
  `score` value the reader page receives (0-1 becomes 0-100) and I don't know
  what the reader expects. `Decimal` keeps the existing scale. If you want
  percentages, it is a one-line change in `related()`, but it is a contract
  change.
- **Not done:** publishing twice against a real table. The ground rules
  forbid deploying or publishing to an external service. The seeded test
  covers the same code path locally, but it runs against `FakeTable`, not
  DynamoDB. Please run one real double-publish after deploying to confirm.
