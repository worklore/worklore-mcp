# Why the second publish returned 500, and the fix

## Cause

`similarity()` in `src/app.py` returned a Python float:
`round(0.7 * tag_score + 0.3 * word_score, 4)`. That float lands in
`item["similar"][i]["score"]` via `related()`, and `publish()` feeds the whole
item to DynamoDB's `put_item`.

DynamoDB (via boto3's `TypeSerializer`) rejects floats outright:
`TypeError: Float types are not supported. Use Decimal types instead.`
— exactly the error in `logs/error.log`.

The first publish survived only because the table was empty: with no existing
stories, `related()` returns `[]`, so no score is ever computed and no float
ever reaches the serializer. The bug only exists once there is data to score,
which is why it appeared on the second write and then on every write after
(`logs/error.log` lines 3–36: two consecutive 500s after one clean 201).

## Fix

`src/app.py`, `similarity()` now returns `Decimal(str(round(..., 4)))` instead
of the raw float. The conversion goes through `str()` so the stored value is
the exact rounded decimal (e.g. `Decimal('0.4029')`), not the binary-float
artifact a direct `Decimal(float)` conversion would carry. `Decimal` is fully
supported by DynamoDB and preserves the existing 0–1 score semantics; sorting
in `related()` is unaffected.

## Why it can't come back

`tests/test_publish.py` gains `test_publish_second_story_with_existing_record`:
it seeds the table with one story and publishes a second, so the
state-dependent scoring path executes under test (the old suite only ever
exercised the empty-table path, which is why the bug shipped). The test also
asserts the stored score is a `Decimal`, pinning the type at the boundary. The
fake table (`tests/fake_dynamo.py`) validates types the way boto3 does, so any
future float reaching an item fails the test the same way a real table would.

Verified: `python3 -m unittest discover tests` — 2 tests pass; three
consecutive publishes through `handler()` all return 201.

## Which parts of the colleague's note applied

Applied directly — the note described this exact failure, and three of its
points carried over:

- The root cause is identical: DynamoDB rejects Python floats, and the
  first write only succeeds because the empty table means no score is
  computed. The "bug does not exist until the data does" framing pointed
  straight at `similar()` being empty on the first publish.
- The testing lesson: the old test only exercised the empty-database path,
  so it now seeds a record before testing the write — the populated path is
  the real path.
- The verification step "publish twice": reproduced pre-fix (second publish
  raised the exact `TypeError` from the log) and re-verified post-fix through
  the `handler()` entry point.

Ignored / adapted:

- The note's actual code fix (scores as integer percentages) was not taken:
  it would change the stored value's meaning. Converting to `Decimal` at the
  computation site fixes the serializer error while keeping the 0–1 score
  format the item schema (`similar: [{slug, score}]`) already uses.
- The "grep for `round(` and `/` feeding item dicts" check: done mentally
  during the fix — `similarity()` was the only float producer reaching an
  item (`published_at` is already `int`).
