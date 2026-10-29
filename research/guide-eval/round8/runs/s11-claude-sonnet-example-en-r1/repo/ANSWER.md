# Why the second publish returns 500

## Cause
`similarity()` in `src/app.py` returned a Python `float` (`round(0.7*tag + 0.3*word, 4)`).
`publish()` stores those scores in `item["similar"]`, and boto3's DynamoDB
serializer rejects floats (`TypeError: Float types are not supported. Use Decimal types instead.`,
see `logs/error.log`). The first publish scans an empty table, so `related()`
returns `[]` and no float is ever written. From the second publish on, there are
existing stories, scores exist, and `put_item` fails. `handler()` catches the
exception and returns 500.

## Fix
- `similarity()` now returns `Decimal(str(round(..., 4)))`, so the score keeps its
  4-decimal precision and is storable. (The note's integer percentage would also work; Decimal avoids changing the stored scale.)
- Added tests that exercise the populated-table path (second and third publish via
  `publish()` and `handler()`). The fake table rejects floats like boto3 does, so this
  regression now fails in tests (I confirmed the logic by reasoning; the new tests pass with the fix).

## Colleague's note: what applied
- Applied: root cause (floats from computed similarity scores, only hit when the table is non-empty), converting at the boundary, and the seeded/second-write test.
- Not applied: the integer-percentage fix (chose Decimal instead); the "publish twice against a real table" step, since I may not touch external services.
- Not addressed: `scan()` is unpaginated (1 MB per page on a real table), so `related()` only sees the first page of stories at scale. Separate issue, not part of this 500.
