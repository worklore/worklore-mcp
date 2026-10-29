# Second publish returns 500

## Cause
`similarity()` in `src/app.py` returns `round(..., 4)`, a Python float. `publish()` stores
the top matches as `similar: [{slug, score}]`, so the float goes into `put_item`.
boto3 refuses floats: `TypeError: Float types are not supported. Use Decimal types instead.`
The first publish scans an empty table, so `similar` is `[]` and no float exists. From the
second publish on there are matches, so the float is written and the handler returns 500.
The existing test only published once, to an empty table, so it never ran this path.

## Fix
- `similarity()` now returns an integer percent (`round(100 * ...)`). DynamoDB accepts ints.
- Added tests that publish a second story into a populated table (checks the score is an `int`)
  and that the handler returns 201 twice. `FakeTable` rejects floats the way boto3 does, so
  reintroducing a float fails the tests.

## Colleague's note
Applied: the diagnosis (the float only appears once data exists), the int-percent fix, and
the advice to seed the table before testing a write. Not applied: the grep for `round(`
and `/` (I read the single file instead) and the real-table publish (not allowed here).

## Not changed
`publish()` uses one un-paginated `scan`, so once the table passes 1 MB the related-story
list will silently be computed from partial data. That is a separate issue.
