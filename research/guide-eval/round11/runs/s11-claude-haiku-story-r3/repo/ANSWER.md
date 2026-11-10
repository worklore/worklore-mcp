# Why the second publish returns 500

## Cause

`publish()` stores each story with a `similar` list: the top three existing
stories, each with a `score`. `similarity()` in `src/app.py` computes that score
as `round(0.7 * tag_score + 0.3 * word_score, 4)`. Division in Python produces a
`float`, and `round(x, 4)` still returns a `float`.

DynamoDB rejects Python floats. boto3 raises
`TypeError: Float types are not supported. Use Decimal types instead.` when it
serializes the item.

The first publish has an empty table. `related()` has nothing to score, so
`similar` is `[]` and no float is ever written. The second publish is the first
one with existing stories to compare against, so it writes a float and fails.
`logs/error.log` shows exactly this: the first story stored with `similar=0`,
and the next two publishes fail with the float error.

The failed write did not store anything, so the table only contains the first
story. The story that failed still needs to be published again after the fix is
deployed.

## Fix

- `src/app.py`: added `to_dynamo()`, which recursively converts every `float` to
  `Decimal(repr(value))`. `publish()` now calls `table.put_item(Item=to_dynamo(item))`.
  Conversion happens at the one write boundary, so a float computed anywhere in
  the item is covered, not just the scores that exist today. `repr` keeps the
  exact shortest decimal, so `0.1234` is stored as `Decimal('0.1234')` and the
  scores keep their precision.
- `tests/test_publish.py`:
  - `test_second_publish_with_seeded_table` seeds one story, publishes a second
    one that has a non-empty `similar` list, and checks that the stored score is a
    `Decimal`. This is the path the existing first-write test never reached.
  - `test_handler_second_publish_returns_201` runs the same two-publish sequence
    through `handler()`, which is what produced the 500.
  - `test_to_dynamo_converts_floats_recursively` covers the converter.

Verification:

- `python3 -m unittest discover tests`: 4 tests, all pass.
- Against the original `src/app.py`, the new tests fail (1 failure, 2 errors),
  so they reproduce the bug.
- A standalone script that publishes twice against the in-memory table: the
  second publish fails on the original code and succeeds on the fix.

## Colleague's note: what applied and what did not

Applied:

- The bug only appears once the table has data. The first-write test never
  exercised the populated path, so the seeded-table test was added.
- Computed values (here, similarity divisions and `round()`) are floats and must be
  converted at the write boundary. The grep for `round(` and `/` feeding item
  data finds `similarity()` (lines 27, 29, 30), and all of them flow into
  `similar`. The other item fields (`published_at` is `int(time.time())`, `tags`
  and `body` are strings) are not floats.
- Decimal instead of a float is the fix the note recommends.

Not applied:

- The note's fix converts scores to integer percentages. I kept the exact
  scores as `Decimal` so the API response and stored values are unchanged. Using
  percentages would change what the data means and is a product decision.
- "Publish twice against a real table" was not done. I have no AWS access here,
  and I was not allowed to deploy or publish to an external service. The in-memory
  table in `tests/fake_dynamo.py` validates types the way boto3 does, and that is
  the check I ran.

## Not done

- No deploy. The fix needs to be deployed, and then the failed story can be
  published again.
