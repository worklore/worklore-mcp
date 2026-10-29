# Second publish returns 500: Python float written to DynamoDB

## Cause

`publish()` stores each story with `similar`: the top three existing stories and
their scores. The score comes from `similarity()`, which returns
`round(0.7 * tag_score + 0.3 * word_score, 4)`. That is a Python `float`.

- **First publish:** the table is empty, so `related()` returns `[]`. No float
  is in the item, and the write succeeds (`logs/error.log`, 09:14:02, 201).
- **Second publish:** `existing` has one story, so `similar` holds
  `{"slug": ..., "score": <float>}`. boto3's `TypeSerializer` rejects floats:
  `TypeError: Float types are not supported`. `handler()` catches it and returns
  500 (`logs/error.log`, 09:21:47 and 09:22:10).

The test suite never reached the bug. `tests/test_publish.py` published into an
empty `FakeTable`, so `similar` was always empty. `FakeTable.put_item` already
rejects floats, but nothing ever gave it one. The bug depends on state, and the
only test ran with no state.

Reproduced locally: with the original code, publishing one story and then a
second one raises the same `TypeError`. The original test suite passed.

## Fix

`src/app.py`, in `related()`, the score is converted to `Decimal` at the point
it enters the item:

```python
scored.append({"slug": other["slug"], "score": Decimal(str(similarity(story, other)))})
```

`Decimal(str(x))` keeps the value exactly as rounded (for example `0.4167`),
so the stored number has the same 4 decimal places as before. Sorting still
works, since `Decimal` compares with `Decimal`. `similarity()` still
returns a float, so the rest of the code is untouched.

## Test that stops it coming back

`tests/test_publish.py::test_second_publish_with_related_story_is_storable`
seeds one story, publishes a second that shares a tag, and checks that:

- the second write succeeds,
- `similar[0]` points to the seeded story,
- `score` is a `Decimal`,
- both items are in the table.

Against the original `app.py` this test errors with the `TypeError`. With the
fix, both tests pass:

```
python3 -m unittest discover tests
Ran 2 tests ... OK
```

## Which parts of the colleague's note applied

- **Applied: trace the values that feed the write.** I grepped `src/app.py` for
  `round(`, `/`, `float(`, and `time.time(`. The float sources are the division
  in `similarity()` (lines 28 and 30) and `round()` (line 31), which reach the
  item through `score`. `published_at` is already `int(time.time())`.
- **Applied: seed the table and test the second write.** This is the test
  added above. It is the most important part: it exercises the path that only
  runs once data exists.
- **Applied: convert at the boundary.** I used `Decimal`, not the integer-percent
  change in the note. Integer percentages would change what `score` means in the
  stored data, and the colleague's case may not have had that constraint. Here
  the 4-decimal value is kept.
- **Not applied: publish twice against a real table.** The ground rules say not
  to publish or report to any external service, so I did not run this. It is
  still the most direct check. Run it after deploying, or in a dev stack.
- **Not applied: the note's "every write-path test" rule.** This repo has one
  write path, `publish()`, and it now has both an empty and a seeded test.

## Not fixed (outside this bug)

- `validate()` checks `slug`, `title`, and `body` but not `tags`. A JSON request
  with a numeric tag, such as `"tags": [1.5]`, would put a float in the item
  (`sorted(set(tags))`). That fails on the first publish, too, so it is not
  state-dependent. A type check on `tags` would prevent it.
- `similarity()` and `related()` scan the whole table on every publish. That is
  not a correctness issue here, but it grows with the library.
