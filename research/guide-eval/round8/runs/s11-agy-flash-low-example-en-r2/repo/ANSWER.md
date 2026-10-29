# Root Cause and Fix Analysis

## Cause of the Bug
When a story is published for the very first time, the DynamoDB `stories` table is empty (`scan()` returns `[]`). Consequently, `related(story, existing)` returns an empty list `[]`, and no similarity scores are computed or included in `item["similar"]`. The item is saved cleanly because no float attributes are present.

On any subsequent publish, existing stories are fetched from DynamoDB. `similarity(story, other)` computes the story similarity score using floating-point arithmetic and `round(..., 4)`. This float score was stored in `item["similar"]` (e.g. `[{"slug": "...", "score": 0.4567}]`). Boto3's DynamoDB serializer (`TypeSerializer`) does not permit Python `float` values, raising:
```
TypeError: Float types are not supported. Use Decimal types instead.
```
This uncaught exception caused `app.handler` to log `publish failed` and respond with HTTP status `500 Internal Server Error`.

---

## The Fix
1. **Convert float similarity score to `Decimal` in `src/app.py`**:
   Imported `from decimal import Decimal` and updated `similarity(a, b)` to return `Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))`. DynamoDB natively serializes `Decimal` types to numeric attributes (`N`).

2. **Add state-dependent tests in `tests/test_publish.py`**:
   Added regression tests (`test_publish_second_story_succeeds_with_similarity_scores` and `test_handler_publish_twice`) that publish a second story onto a pre-populated table to verify that similarity scores are serialized and stored without error.

---

## Colleague's Note: What Applied and What Was Ignored

### What Applied:
- **Root cause diagnosis**: The realization that the first publish succeeded because the table was empty (no scores or matches computed), while the second publish populated `similar` with Python `float` scores that boto3/DynamoDB rejects with `TypeError: Float types are not supported. Use Decimal types instead.`
- **Tracing computed values**: Traced division/rounding in `similarity()` feeding into `item["similar"]` written via `table.put_item(Item=item)`.
- **Conversion at boundary**: Converted the float score to `Decimal` (`Decimal(str(...))`), which DynamoDB supports.
- **Testing strategy**: Seeding/testing against a populated table (publishing twice) so that state-dependent logic actually executes during automated tests.

### What Was Ignored:
- **Integer percentage alternative**: The note mentioned converting scores to integer percentages as one option. We chose `Decimal` to maintain the 4-decimal precision expected by the API model.
- **External table testing / AWS instructions**: Instructions referencing real DynamoDB tables, AWS account setups, and external deployment steps were ignored in accordance with local testing ground rules and `tests/fake_dynamo.py`.
