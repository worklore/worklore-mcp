# Why the second publish returns 500

## Cause
`publish()` stores `similar: [{slug, score}]`, where `score` comes from `similarity()`, which returns a Python `float` (`round(0.7*x + 0.3*y, 4)`). boto3's serializer rejects floats: `TypeError: Float types are not supported. Use Decimal types instead.` (logs/error.log).

The first publish works because the table is empty, so `related()` returns `[]` and no float is in the item. From the second publish on, there are existing stories, so scores are computed and `put_item` fails. The original test only covered the empty-table path, so it never caught this.

## Fix
- `src/app.py`: `related()` converts each score to `Decimal(str(score))` before it goes into the item. This keeps the 4-decimal precision, and sorting still uses the float values.
- `tests/test_publish.py`: added `test_second_publish_with_similar_story`. It seeds one story and then publishes a second, so the scoring path runs. The `FakeTable` rejects floats the way boto3 does. Before the fix this test fails with the same TypeError; after it, it passes.

## How the colleague's note applied
- Applied: the diagnosis (floats are rejected, and the bug only shows once data exists), converting at the boundary, and the seeded-table test for the second write.
- Adapted: the note converted scores to integer percentages. I used `Decimal` instead, so the stored scores keep their precision and the item format doesn't change.
- Not applicable: the grep for `round(`/`/` found only `similarity()`. The note's advice to publish twice against a real table wasn't done here, because I was told not to touch external services.

## Not changed, but worth knowing
`publish()` uses a single `scan()` with no pagination. Once the table passes 1 MB, scoring will only see part of it.
