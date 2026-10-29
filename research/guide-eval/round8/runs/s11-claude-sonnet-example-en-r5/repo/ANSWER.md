# Second publish returns 500

## Cause
`similarity()` in `src/app.py` returns a Python `float` (`round(0.7*a + 0.3*b, 4)`).
`publish()` stores the top matches as `similar: [{slug, score}]`. On the first
publish the table is empty, so `similar` is `[]` and no float is written. From the
second publish on, `similar` holds float scores. boto3 rejects floats with
`TypeError: Float types are not supported. Use Decimal types instead.`, and the
handler turns that into a 500 (see `logs/error.log`). The existing test only
published into an empty table, so it never ran this path.

## Fix
- `src/app.py`: added `to_dynamo()`, which recursively converts floats to `Decimal`
  (via `str`, so 0.4125 stays exactly 0.4125). `publish()` runs the whole item
  through it right before `put_item`. Any float added to the item later is
  converted too, not just `score`.
- `tests/test_publish.py`: added two tests that publish a second story into a
  populated table, one through `publish()` and one through `handler()` expecting 201.
  They fail without the fix and pass with it.

I kept scores as Decimals rather than changing them to integer percentages, so the
stored values keep their precision and the reader page's format doesn't change.

## Colleague's note
Applied:
- The diagnosis. Floats only appear once existing data produces scores.
- Converting at the write boundary.
- Seeding the table before testing a write.

Not applied:
- Integer percentages. I used Decimal instead.
- The real-table double publish. Nothing outside this directory was touched, and the
  fake table rejects floats the same way boto3 does.
- The grep for `round(` and `/`. The repo is one file, and I read it directly.
