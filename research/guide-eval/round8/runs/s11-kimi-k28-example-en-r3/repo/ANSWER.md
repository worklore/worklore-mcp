# Why the second publish returned 500

## Cause

`publish()` stores each story together with its three most similar existing
stories (`similar: [{slug, score}]`). The score comes from `similarity()`
(`src/app.py:30`), which computes a Jaccard-style ratio and returns
`round(0.7 * tag_score + 0.3 * word_score, 4)` — a Python `float`.

DynamoDB (via boto3's `TypeSerializer`) does not accept floats; it only accepts
`int` and `decimal.Decimal` for numbers. So any `put_item` carrying a float
fails with:

    TypeError: Float types are not supported. Use Decimal types instead.

That is exactly the error in `logs/error.log` (`app.py` line 63,
`table.put_item(Item=item)`).

**Why only the second publish crashed:** the first publish ever finds an empty
table, so `related()` returns `[]` and no float ever reaches DynamoDB — the
first write succeeds (see `similar=0` in the log's first line). Every
subsequent publish computes at least one real similarity score, the float goes
into the item, and the write blows up. The bug existed from the first deploy;
it just needed existing data to become visible. The old test suite only ever
exercised the empty-table path, so it never caught it.

## Fix

One line in `src/app.py:30` — convert the computed score to `Decimal` at the
boundary where it becomes a stored value:

```python
return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
```

Going through `str()` matters: `Decimal(0.2333)` would capture the binary-float
artifact (`0.2332999999...`), while `Decimal(str(...))` stores the exact
rounded value (`Decimal('0.2333')`). I chose `Decimal` over the colleague's
integer-percentage approach to preserve the existing 4-decimal precision of
the scores. The other item fields were audited: `published_at` is already
`int`, everything else is a string — the score was the only float producer.

To keep it from coming back, `tests/test_publish.py` gains
`test_second_publish_stores_similar_scores`: it seeds the table with one story
and publishes a second, so the state-dependent scoring path actually executes
under test and asserts the stored score is not a float. Verified with
`python3 -m unittest discover tests` (2 tests, OK) and by publishing twice
against the fake table — the second publish now stores
`{'slug': '...', 'score': Decimal('0.2333')}`.

## Which parts of the colleague's note applied

- **The diagnosis, verbatim in spirit:** "Float types are not supported" on the
  second write, caused by computed similarity scores, invisible on the first
  write because the table was empty. All of this matched exactly.
- **"Trace every value that feeds a DynamoDB write and flag anything computed
  — divisions, averages, rounded scores":** applied. The score (`/`, `round()`)
  was the only offender; `published_at` (`int(time.time())`) and the strings
  are safe.
- **"Convert to int or decimal.Decimal at the boundary":** applied, with
  `Decimal` rather than `int` to keep the 4-decimal precision (a deliberate
  deviation, see above).
- **"Add one integration test that seeds a record and writes a second one":**
  applied — this is now `test_second_publish_stores_similar_scores`.
- **"My 'it works' test had only ever exercised the empty-database path":**
  applied as the general lesson; every write-path test here now seeds first.

Not applied: nothing in the note was wrong for this case, so no part had to be
discarded — only the int-percentage choice was adapted to Decimal.
