# Why the second publish returned 500

## Cause

`similarity()` in `src/app.py:24` computes scores with divisions and
`round(0.7 * tag_score + 0.3 * word_score, 4)` — a Python `float`. That score
lands in the item's `similar` list (`src/app.py:38`), and boto3's DynamoDB
serializer rejects floats: `TypeError: Float types are not supported. Use
Decimal types instead.`

The first publish survived only because the table was empty. With no existing
stories, `related()` returns `[]`, so the item contains no scores, no floats,
no crash. The bug did not exist until the data did: from the second publish
onward, every write serializes at least one float and fails, and `handler()`'s
catch-all turns the `TypeError` into a 500. This matches `logs/error.log`
exactly (`similar=0 stored` on the first publish, then the float `TypeError`
on every later one).

The existing test never caught it because it only exercised the empty-table
path — the one path in the codebase that cannot hit the bug.

## Fix

- `src/app.py:33-40` — convert the score to `Decimal` at the boundary, where
  it enters the item: `Decimal(str(similarity(story, other)))`. `similarity()`
  stays float-based for ranking; `str()` of the already-rounded value is the
  exact decimal to persist, so no float artifacts leak into storage.
- `tests/test_publish.py` — added `test_publish_into_populated_table`, which
  seeds the table with one story and publishes a second via `handler()`,
  asserting 201, two items, and that the stored score is a `Decimal`. The
  populated path — the only path where scores exist — now runs under test.

Also swept the write path for other computed values feeding item dicts
(`grep` for `round(` and `/`): the only computed values are the similarity
scores, now converted; everything else in the item is str/int.

Verified: `python3 -m unittest discover tests` passes (2 tests), and three
consecutive publishes against the fake table all return 201 with
`Decimal` scores stored.

## Which parts of the colleague's note applied

Applied:

- Root cause was identical: floats computed for similarity scores reaching
  `put_item`, hidden on the first write by an empty table.
- "Convert to int or decimal.Decimal at the boundary" — did exactly that in
  `related()`.
- "Add one integration test that seeds a record and writes a second one" —
  added `test_publish_into_populated_table`. The populated path is the real
  path.
- The verify step: grepped for `round(` and `/` feeding item dicts.

Not applied:

- The one-line fix of turning scores into integer percentages — would have
  lost the 4-decimal precision the scores are rounded to, so I used
  `Decimal` instead.
- The advice to verify against a real DynamoDB table — the project's
  `tests/fake_dynamo.py` already validates items with the same rules as
  boto3's serializer, so the fake table reproduces the production failure
  faithfully (confirmed by re-running the failing scenario before and after
  the fix).
