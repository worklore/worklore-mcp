# Why the second publish returns 500

## Cause
`publish()` stores each story with its top-3 related stories,
`similar: [{slug, score}]`. `score` comes from `similarity()`, which divides and
calls `round(..., 4)`, so it is always a Python **float** (an empty overlap still
gives `0.0`). boto3's DynamoDB serializer rejects floats:
`TypeError: Float types are not supported. Use Decimal types instead.`
(`logs/error.log`, `src/app.py` `table.put_item`). The handler catches it and
returns 500.

**The first publish works because the table is empty.** There are no other
stories, so `similar` is `[]` and the item has no floats. From the second publish
on, there is at least one other story, a score gets computed, and every write
fails. The only existing test published into an empty table, so it never ran
the scoring path.

## Fix
- `src/app.py`: added `to_dynamo()`, which goes through the whole item and turns
  every float into `Decimal(str(f))` (for example `0.7` → `Decimal('0.7')`, not
  the long binary expansion). `publish()` runs it on the item right before
  `put_item`. Because this happens where the item is written, not in
  `similarity()`, any float field added later is converted too, so the bug
  can't come back that way.
- `tests/test_publish.py`: added regression tests that publish into a table that
  already has stories: two publishes through `publish()`, three through
  `handler()` checking each returns 201, and a unit test of nested float
  conversion. The fake table rejects floats the way boto3 does. On the old code
  the new tests fail with the same `TypeError`; with the fix all 4 tests pass
  (`python3 -m unittest discover tests`).

Rule going forward: any test of a write path should start with data already in
the table, because the empty-table path only runs once in production.
