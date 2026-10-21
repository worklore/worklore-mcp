# Why the second publish returns 500

## Cause

`publish()` stores each story with `similar`: the top matches from the existing
library, each as `{slug, score}`. The score comes from `similarity()`, which
returns `round(0.7 * tag_score + 0.3 * word_score, 4)`. In Python that is a
`float`.

boto3's DynamoDB serializer rejects floats:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The bug sits on the path that only runs when the table already has items:

- **First publish (empty table):** `existing` is `[]`, so `related()` returns
  `[]`. No score is computed, no float is written, and the item stores.
  This is the `201` in `logs/error.log`.
- **Second publish:** `scan()` returns one story, `related()` computes a score,
  and `put_item` gets `similar: [{"slug": ..., "score": 0.4286}]`. The float is
  rejected and the handler returns `500`.

Nothing was partially written. The failed `put_item` never reached DynamoDB, so
the table only holds the first story.

The tests missed this because `test_publish_stores_story` only publishes into an
empty `FakeTable`. The fake already rejects floats the way boto3 does; the test
never reached the code path that produces one.

## Fix

`src/app.py`, in `related()`: the score is converted to `Decimal` before it is
stored.

```python
score = Decimal(str(similarity(story, other)))
```

- `str()` first, so the stored value is the rounded score exactly
  (`0.4286`), not the binary expansion you get from `Decimal(0.4286)`.
- The value is the same number as before, so the stored data and the meaning of
  `score` don't change.
- `similarity()` still returns a float internally; only the value that crosses
  into the item is converted, and that is the only place floats reach a write.

### Keeping it from coming back

- `tests/test_publish.py::test_publish_second_story_stores_related_scores`:
  seeds the table with one story, publishes a second, and asserts the scores
  are `Decimal` and the write succeeds. This is the path that failed in
  production.
- `tests/test_publish.py::test_related_scores_are_never_float`: five existing
  stories, asserts every score in the top `TOP_N` is `Decimal`.

Verification:

- `python3 -m unittest discover tests`: 3 tests, all pass.
- The two new tests against the original `src/app.py`: 1 failure, 1 error,
  so they catch the bug.
- Grep for `round(`, `/` and `**` in `src/app.py`: the only computed values are
  inside `similarity()`. The only value that reaches an item is `score`, which
  now goes through `Decimal`.

## What I did not do

- **No publish against a real table.** This environment has no AWS access, and
  publishing to an external service is outside the ground rules. The seeded
  test exercises the same `put_item` type check as boto3, but it is not a
  substitute for publishing twice to the real `stories` table after deploy.
- **No deploy.** The fix is only in the working tree; nothing is committed.

## Colleague's note: what applied

- **Applied:** the core lesson. Scoring-style code has a second path that
  first-write tests never touch, and the empty-table path only runs once. The
  new tests seed a record before the second write.
- **Applied:** convert at the boundary, here `related()`, and grep for
  `round(` and `/` feeding item dicts.
- **Applied, partly:** the "publish twice" check is the right final check, but
  I could only do the seeded-table version here (see above).
- **Not applied:** converting the score to an integer percentage. That changes
  what the stored value means and would lose precision the reader might use.
  `Decimal` keeps the same number. Use the integer approach only if you want
  whole percentages for the UI.

## Caveat for the reader side

Once `similar` contains `Decimal` scores, DynamoDB returns those numbers as
`Decimal` when read through boto3. `json.dumps` cannot serialize `Decimal`, so
any reader code that returns stored items as JSON will need a conversion, for
example `default=float` or `default=str`. This repo has no read path, so nothing
here changes, but it will break there the first time it reads a story that has
`similar` filled in.
