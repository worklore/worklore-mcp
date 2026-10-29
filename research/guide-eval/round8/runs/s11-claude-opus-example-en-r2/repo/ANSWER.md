# Why the second publish returns 500

## Cause

`publish()` (`src/app.py`) stores each story with its top-3 related stories,
`similar: [{slug, score}]`. `score` comes from `similarity()`, which returns
`round(0.7 * tag_score + 0.3 * word_score, 4)`. That is a Python **float**, and
boto3's DynamoDB serializer rejects floats:
`TypeError: Float types are not supported. Use Decimal types instead.`
(`logs/error.log`, `app.py` line 63, `table.put_item`).

The first publish worked because the table was empty. `related()` had nothing
to score, `similar` was `[]`, and the item held no floats (the log shows
`similar=0`). Every publish after that has at least one existing story, so it
gets a float score and fails. Even a zero score is `0.0`, which is still a float.
The only test published one story into an empty table, so it never ran the
scoring code.

## Fix

1. **A conversion step before the write** (`to_dynamo()` in `src/app.py`). It
   walks the whole item just before `put_item` and turns every float, at any
   depth, into a `Decimal`. Because it covers the whole item and not just the
   `score` field, a float added later (an average, a ratio, a new score) can't
   bring this crash back.
2. **`Decimal(str(x))`, not `Decimal(x)`.** `Decimal(0.1)` is a 55-digit
   binary expansion. DynamoDB keeps at most 38 significant digits, so boto3
   raises `Inexact`. I checked this against the installed boto3
   `TypeSerializer`: `Decimal(0.1)` fails, and the converted item serializes as
   `{'N': '0.425'}`.
3. **Scores keep their 0–1 scale** with 4 decimal places. Anything reading
   `similar[].score` sees the same values as before; no format change.
4. **Tests that use a table with data in it** (`tests/test_publish.py`):
   - publish twice through `handler()` and expect 201 both times, with a
     `Decimal` score between 0 and 1;
   - publish into a table of 5 stories, so the top-3 cut is used;
   - unit test: `to_dynamo` converts nested floats exactly.

   With the old `app.py`, the new tests fail (1 failure, 2 errors). With the
   fix, all 4 pass (`python3 -m unittest discover tests`).

## Which parts of the colleague's note applied

- **Applied:** the diagnosis is the same. A float similarity score reaches
  `put_item`, and the first write gets through only because the empty table
  produces no scores. The lesson also applied: the existing test only covered
  the empty table, so the new tests publish into a table that already has
  stories. I followed the advice to trace computed values (`/`, `round(`)
  into the item; `similarity()` is the only place they occur.
- **Adapted:** the note changed scores to integer percentages. I used
  `Decimal` instead, so the stored scale (0–1) stays the same. I also convert
  the whole item in one place rather than patching the one field, because that
  is what prevents a repeat.
- **Not done:** "publish twice against a real table". The instructions said
  not to touch external services. The in-memory table in the tests rejects
  floats the same way boto3 does, and I also ran the converted item through
  boto3's own serializer locally. The Lambda/deploy details in the note didn't
  matter here.
