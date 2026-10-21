# Second publish returns 500

## Cause
`publish()` stores each story with its top-3 related stories, `similar: [{slug, score}]`.
`similarity()` returns `round(0.7*tag + 0.3*word, 4)`, which is a Python **float**, and
boto3 refuses floats in DynamoDB items:
`TypeError: Float types are not supported. Use Decimal types instead.` (logs/error.log, `app.py` `put_item`).

The first publish worked only because the table was empty: `scan()` returned no
items, so `similar` was `[]` and nothing in the item was a float (log line: `similar=0`).
From the second publish on there is at least one existing story, so a float score
ends up in the item and every publish fails. The handler's generic `except Exception`
turns that into a 500.

The existing test only published into an empty table, so it never ran the scoring path.

## Fix
- `src/app.py`: new `to_dynamo()` converts every float to `Decimal(str(x))`, going
  through nested dicts and lists. `publish()` runs the whole item through it right
  before `put_item`. Scores stay exact (`0.4083` comes back as `Decimal('0.4083')`), and
  because the conversion happens on the whole item at the boundary, not just on
  `score`, a float field added later can't bring the crash back.
- `tests/test_publish.py`: new tests (1) publish into a seeded table and check the
  stored score is a non-zero `Decimal`, (2) call `handler` twice and expect 201 both
  times, (3) check `to_dynamo` on nested floats. Against the old `app.py` these fail
  with the same `TypeError` as production; with the fix all 4 tests pass
  (`python3 -m unittest discover tests`).

## Which parts of the colleague's note applied
- **Applied:** the diagnosis is the same. A float similarity score breaks `put_item`,
  and it only shows up once the table has data. I also used the lesson about testing
  write paths against a seeded table, and the advice to convert at the boundary
  (to `Decimal`).
- **Changed:** the note turned scores into integer percentages. I used `Decimal`
  instead so the score's 4-decimal precision is kept, and I convert the whole item
  in one place so a future float field is covered too.
- **Not done:** "publish twice against a real table". The ground rules forbid
  touching external services, and `tests/fake_dynamo.py` already rejects floats the
  same way boto3 does. The note's Lambda/boto3 setup steps and grep checklist were
  general advice; the only float source here is `similarity()`. `published_at` is
  already an `int`.
