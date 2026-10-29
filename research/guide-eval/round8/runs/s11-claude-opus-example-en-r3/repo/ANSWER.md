# Why the second publish returns 500

## Cause

`publish()` stores each story with `similar: [{slug, score}]`. `score` comes
from `similarity()` (`src/app.py`), which divides two set sizes and then calls
`round(0.7 * tag_score + 0.3 * word_score, 4)`. That always gives a Python
**float**, even when the score is `0.0`. boto3 refuses to serialize floats
(`TypeError: Float types are not supported. Use Decimal types instead.`). The
exception falls through to the generic `except Exception` in `handler()`, which
returns 500.

The first publish worked because the table was empty. `scan()` returned no
items, so `similar` was `[]` and the item held no floats (log:
`similar=0 stored`). From the second publish on there is at least one existing
story, so a float score gets into the item and `put_item` fails. Every publish
after the first fails the same way, which matches both 500s in
`logs/error.log`. The table holds only the first story.

The existing test missed it because it only publishes into an empty
`FakeTable`. The fake does reject floats the same way boto3 does, but the test
never ran the code that computes scores.

## Fix

- **`to_dynamo()` at the write boundary** (`src/app.py`). The item is passed
  through it before `put_item`. It walks the whole item and turns every float
  into `Decimal(str(value))`, so `0.4667` is stored as `0.4667` and not as a
  binary-float approximation. NaN and infinity have no DynamoDB form, so they
  raise `ValueError` (400) with a clear message instead of failing inside
  boto3. Converting here and not only in `similarity()` keeps the bug from
  coming back: any float added to the item later, at any depth, gets converted
  too. Scores stay on the same 0–1 scale, so the reader page needs no change.
- **Tests that use a table with data in it** (`tests/test_publish.py`):
  - `test_second_publish_with_existing_story`: seeds one story, publishes a
    related one, and checks that both are stored and the score is a non-zero
    `Decimal`.
  - `test_handler_returns_201_on_every_publish`: five publishes in a row
    through `handler()`, each expected to return 201.
  - `test_to_dynamo_converts_nested_floats`: tests the converter on its own,
    including the NaN case.

  I ran the new tests against the original `app.py` and they fail with the
  same `TypeError` as production. With the fix, all 4 tests pass
  (`python3 -m unittest discover tests`).

## Which parts of the colleague's note applied

**Applied:**
- The diagnosis: a computed float in the item, hidden on the first write
  because the table was empty. It is the same bug, even the same kind of
  feature (similarity scores / top matches).
- "Trace every value feeding the write; flag divisions and `round(`." The only
  ones are in `similarity()`.
- "Convert to int or Decimal at the boundary." I used Decimal at the
  `put_item` boundary.
- "Seed the table with one record, then test the write." Done.

**Not applied:**
- Turning scores into integer percentages. That would change the stored scale
  (0–1 to 0–100) that readers of `similar` rely on. Decimal keeps the
  meaning, and a converter at the boundary covers future fields too, where a
  one-line change in `similarity()` would not.
- "Publish twice against a real table." Not done: the ground rules forbid
  deploying or touching external services. The `FakeTable` in the repo checks
  types the way boto3's serializer does, and it reproduces the production
  error exactly.

## Not fixed: possible future problem

`publish()` makes one `scan()` call and ignores `LastEvaluatedKey`. Once the
table is larger than 1 MB, related stories will be picked from only part of the
library. This is unrelated to the 500, so I left it alone.
