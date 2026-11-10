# Second publish returns 500: float scores reach DynamoDB

## Cause

`publish()` stores each story with `similar`: the top matches from existing
stories, each as `{slug, score}`. `score` comes from `similarity()`, which
returns `round(0.7 * tag_score + 0.3 * word_score, 4)`. Division in Python
produces a `float`, so `score` is a float.

On the first publish the table is empty. `related()` has nothing to score, so
`similar` is `[]` and no float is written. The publish succeeds (log line
`similar=0 stored`, 201).

On the second publish the table has one story. `related()` scores it, and
`similar` becomes `[{"slug": ..., "score": 0.0}]`. `table.put_item` then gets a
Python float inside a nested list and boto3 raises
`TypeError: Float types are not supported. Use Decimal types instead.` The
handler catches it as a generic `Exception` and returns 500
(`logs/error.log`, 09:21:47 and 09:22:10).

The existing test only published into an empty `FakeTable`, so the scoring
branch never ran. The fake already rejects floats, so the test suite would have
caught this had it covered a populated table.

## Fix

`src/app.py`:

- Added `to_dynamo(value)`, which recursively converts every `float` to
  `Decimal(str(value))`. `str()` keeps the digits that `round(..., 4)` produced
  (`0.3333` stays `0.3333`).
- `publish()` calls `table.put_item(Item=to_dynamo(item))`. This is the only
  write, so every float in the item is converted before it reaches boto3. A
  float added later (a new score, an average, a ratio) is converted
  automatically and cannot produce a 500 on the second publish.

`tests/test_publish.py`:

- `_seeded_table()` publishes one story first. Each write-path test starts
  from it, so the populated-table branch runs.
- `test_publish_with_existing_story_stores_float_free_item`: the second publish
  stores its match as a `Decimal` score.
- `test_handler_second_publish_returns_201`: reproduces the production path
  through `handler()`. It failed with 500 before the fix.
- `test_similar_scores_are_decimal_in_populated_table`: a third publish checks
  that every stored score is a `Decimal`.

Result: `python3 -m unittest discover tests -v` runs 4 tests, all passing. Before
the fix, the handler test returned 500 and the populated-table tests raised the
same `TypeError` as the log.

Nothing was deployed, published, or sent to any external service.

## Colleague's note: what applied

- **Applied:** the root cause pattern. Floats from computed scores reach the
  write only when existing state makes the scoring path run, and the empty-table
  test hid it. The "seed the table before testing the write path" advice is
  applied in `_seeded_table()`.
- **Applied:** DynamoDB accepts `Decimal` (and `int`), and the fix converts to
  `Decimal`.
- **Not applied:** the integer-percentage change. This codebase's `score` is a
  0–1 similarity ratio, and changing it to 0–100 integers would change the data
  contract for readers without being needed to fix the error. `Decimal` keeps the
  existing values and meaning.
- **Not applied:** "one-line change." The one-line fix would have been a
  per-score conversion. The boundary conversion in `to_dynamo` is a small
  addition that also covers future floats in the item.
- **Checked, no floats:** `published_at` (`int(time.time())`), `tags`, `slug`,
  `title`, `body`, and the `similar` slugs are all `int` or `str`. Only `score`
  was a float in this item.
