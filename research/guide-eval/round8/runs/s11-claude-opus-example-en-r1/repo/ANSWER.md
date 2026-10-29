# Why the second publish returns 500

## Cause

`publish()` saves each story together with its top‑3 `similar` stories, and each
of those has a `score`. `similarity()` returns
`round(0.7 * tag_score + 0.3 * word_score, 4)`, which is a Python **float**.
boto3 doesn't accept floats in DynamoDB items. `put_item` raises
`TypeError: Float types are not supported. Use Decimal types instead.`
(`src/app.py:63` in the log). `handler()` catches that as a generic exception
and returns 500.

The first publish worked only because the table was empty. `related()` had
nothing to score, so `similar` was `[]` and the item had no floats (see the log:
`similar=0 stored`). Every publish after that has at least one existing story,
so there's at least one float score. This happens even for unrelated stories:
`0.7 * 0 + 0.3 * 0` is `0.0`, which is still a float. So every publish after the
first one fails, which matches the two 500s in the log. The existing test missed
it because it only ever published into an empty table.

## Fix

- **`src/app.py`: added `to_dynamo()` and used it on the item before `put_item`.**
  It goes through the whole item and turns every float into
  `Decimal(str(x))`. That keeps the 4‑decimal score exactly (`0.4667`, not a
  binary‑float tail). NaN and ±inf are rejected as `ValueError`, because DynamoDB
  can't store them either. I did the conversion once for the whole item instead
  of only on `score`, so a float added to the item later can't bring this back.
- **`src/app.py` `validate()`: the request body now has to be a JSON object, and
  `slug`, `title`, `body` and `tags` are type‑checked.** Before, client JSON such
  as `"title": 1.5` would also have put a float into the item, and
  `"body": [..]` or `"tags": [1.5, "x"]` would have crashed with a 500. Those
  requests now get a 400.
- **`tests/test_publish.py`: added tests that seed the table first.** They
  publish into a table that already has stories, publish through `handler()`
  three times in a row and expect 201 each time, cover the zero‑score case,
  check ranking and the `TOP_N` limit, and check bad input and `to_dynamo`.
  `tests/fake_dynamo.py` already rejects floats the same way boto3 does, so these
  tests fail on exactly this bug: with the old `app.py`, 7 of the 8 fail. With
  the fix, all 8 pass (`python3 -m unittest discover tests`).

Existing data needs no migration. No item was ever stored with a float, because
every write that had one failed.

## Which parts of the colleague's note applied

**Applied:**
- **Diagnosis.** It's the same bug: computed similarity scores are floats, and
  they only show up once the table has data, so the first write works and every
  later one fails.
- **"Trace every computed value that feeds a write and convert at the
  boundary."** I did this, and made the boundary cover the whole item instead of
  just one field.
- **"Seed the table before testing the write."** This is now the main kind of
  test (`seeded_table()`).
- **Grep for `round(` / `/` feeding item dicts.** The only places are in
  `similarity()`. `published_at` is already `int(time.time())`.

**Not applied:**
- **The one‑line fix of storing scores as integer percentages.** I used
  `Decimal` instead. Integer percentages would round 0.4667 down to 47 and change
  what `score` means for whatever reads it. `Decimal` keeps the value and the
  meaning, and a whole‑item conversion protects future fields too, which one
  `int()` call wouldn't.
- **"Publish twice against a real table."** I didn't do this. The ground rules
  rule out touching external services, so I verified against the in‑repo fake
  table, which copies boto3's type check. A real two‑publish test is still worth
  running in a non‑production environment before the next deploy.
- **The AWS Lambda and "related items" framing.** That fits this service, but it
  wasn't needed for the fix.
