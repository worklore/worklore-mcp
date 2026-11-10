# Second publish returns 500: float score written to DynamoDB

## Cause

`publish()` in `src/app.py` stores each story with `similar`: its three most
similar existing stories, each as `{slug, score}`.

- `similarity()` computes the score as a float: two divisions (lines 44, 46)
  and `round(..., 4)` (line 47).
- On the first publish the table is empty, so `related()` has nothing to score.
  `similar` is `[]` and no float is ever written. The log confirms this:
  `publish slug=why-my-cron-ran-twice similar=0 stored`.
- On the second publish there is one existing story, so `similar` holds a float
  score. `table.put_item(Item=item)` then raises
  `TypeError: Float types are not supported. Use Decimal types instead.`
  The handler catches it and returns 500 (`logs/error.log`, 09:21:47 and
  09:22:10).

The existing test only publishes into an empty table, so it never reached the
path with a score. That is why it passed.

## Fix

1. **`src/app.py`**: added `to_dynamo(value)`, which converts every float to
   `Decimal(str(value))` at any depth of the item. `publish()` now calls
   `table.put_item(Item=to_dynamo(item))`. The conversion sits at the write
   boundary, so any float added later is converted too, not only the score.
   Scores stay the same numbers: `0.4286` is stored as `Decimal("0.4286")`.
2. **`tests/test_publish.py`**: three new tests.
   - `test_second_publish_with_related_story_is_stored`: seeds one story and
     publishes a second one that matches it. This is the path that was never
     tested. It also checks that the stored score is a `Decimal`.
   - `test_handler_second_publish_returns_201`: the same sequence through
     `handler()`, asserting 201 instead of 500.
   - `test_to_dynamo_converts_floats_at_any_depth`: unit test for the converter.

I used `Decimal` rather than integer percentages. Integer percentages would
change the score values the reader page sees, which I could not check from this
repo.

## Verification

- Before the fix, the repro (seed one story, publish a second) fails with the
  production TypeError, and both new publish tests fail (the handler test
  returns 500).
- After the fix, `python3 -m unittest discover tests -v` runs 4 tests, all OK.
  The repro now succeeds for both publishes.
- `grep -nE "round\(|/ |/\(|float\("  src/app.py` finds only the three lines in
  `similarity()`. Those are the only float sources, and they now pass through
  `to_dynamo()`. `published_at` is already an `int`.

## Not done

- **Publishing twice against a real table.** I did not do this. I have no AWS
  access here, and the ground rules say not to publish or deploy to an external
  service. To check it: deploy, publish one story, then publish a second one
  that shares a tag with it. The second publish should return 201 and the
  item in `stories` should contain `similar[].score` as a Number.
- **Scan pagination (not a fix for this bug, but a related risk).**
  `publish()` calls `table.scan(...)` once and reads only the first page, which
  is capped at 1 MB. Once the library is large, `similar` will silently miss
  matches. Fixing it means following `LastEvaluatedKey`, or moving the lookup
  to a query.

## Colleague's note: what applied

- **Applied:** the root cause pattern. The first write runs an empty-state path,
  and first-write tests never reach the state-dependent code. The fix was a
  seeded-table test.
- **Applied:** converting computed values to `int` or `Decimal` at the write
  boundary. I chose `Decimal` (see above).
- **Applied:** the grep for `round(` and `/` feeding item dicts. It found the
  three lines in `similarity()`.
- **Applied:** the seeded-table integration test.
- **Not applied:** publishing twice against a real table. It needs AWS access and
  is outward-facing, so I left it to you (see "Not done").
- **Not applicable:** the blog framing, the `reproducible` and `tags` metadata,
  and the "dedup / counters" examples. The repo has no dedup or counter code.
