# Why the second publish returned 500

## Cause

`similarity()` in `src/app.py:30` returns a Python `float`
(`round(0.7 * tag_score + 0.3 * word_score, 4)`), and that value lands in the
`similar[].score` attribute of the item passed to `table.put_item()`. DynamoDB
accepts only `int`/`Decimal` for numbers, so boto3 raises
`TypeError: Float types are not supported. Use Decimal types instead.`.

The bug only exists once the table has data. On the first publish the table is
empty, `related()` returns `[]`, the item contains no floats, and the write
succeeds (201 in the log). From the second publish on, `related()` computes a
score for each existing story, a float enters the item, and `put_item` fails —
exactly the 500 + traceback in `logs/error.log`. The code path that crashes is
state-dependent: it runs only when the table is non-empty, so the existing
test (empty table, single publish) never touched it.

Reproduced locally with the in-memory fake table: first publish 201, second
publish 500, same traceback as production.

## Fix

One line in `src/app.py:30` — convert the score to `Decimal` at the boundary,
so no float can ever reach the item:

```python
return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
```

`str(...)` avoids the binary-expansion artifacts of `Decimal(0.35)`-style
conversion, so stored values stay clean (`Decimal('0.35')`). Traced every value
that feeds the item (`slug`, `title`, `tags`, `body`, `published_at` int,
`similar` scores) — the score was the only computed/float value, so this one
conversion covers the whole write path.

To keep it from coming back, `tests/test_publish.py` now has two regression
tests that exercise the populated path:

- `test_publish_with_existing_record_stores_decimal_scores` — seeds the table
  with one story, publishes a second, and asserts the stored score is a
  `Decimal` (fails loudly if a float ever comes back).
- `test_handler_publish_twice_returns_201` — publishes two stories through
  `handler()` and asserts 201 both times, mirroring the production failure.

Verified: `python3 -m unittest discover -s tests` — 3 tests, all passing; a
manual double-publish through `handler()` returns 201 twice and stores the
score as `Decimal('0.0')`.

## Which parts of the colleague's note applied

Applied:

- **The diagnosis itself** — identical situation: computed similarity scores
  stored on the item; first write survives only because the table is empty;
  "the bug did not exist until the data did."
- **Trace every value feeding a DynamoDB write and flag computed ones**
  (divisions, blends) as floats-in-waiting. Done: `similarity()`'s score was
  the only one; `published_at` is already an int.
- **Convert at the boundary** rather than reworking the scoring math.
- **The regression-test advice** — "seed the table with one record before
  testing the write; the populated path is the real path." Both new tests do
  this.
- **The verify step's spirit** — grep-style audit of computed values plus a
  seeded-table test (the note's grep for `round(` and `/` points straight at
  `src/app.py:27-30`).

Not applied:

- **Integer percentages instead of floats.** The colleague converted scores to
  ints; here I kept the documented 0–1 score scale (README describes
  `similar: [{slug, score}]` and the reader page consumes it) and used
  `Decimal` instead, which DynamoDB accepts natively. Same one-line shape,
  different boundary type.
- **"Publish twice against a real table."** The repo's `tests/fake_dynamo.py`
  validates items the way boto3's serializer does (per README, deliberately so
  no AWS account is needed), and this failure occurs during client-side
  serialization — before any network call — so the fake reproduces it
  faithfully. Verified with a manual double-publish through `handler()`.

Everything else in the note (Lambda specifics, the date, ground rules) was
context, not instruction; working stayed inside this directory and nothing was
deployed or sent anywhere.
