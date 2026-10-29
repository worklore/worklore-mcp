# Cause and Fix for Second Publish Failure

## Cause
When the first story is published, the DynamoDB table is empty (`existing` items count is 0). As a result, `related(story, existing)` returns an empty list `[]`, and `similar` contains no items.

When a second story is published:
1. `publish()` queries existing stories using `table.scan()`, finding the first published story.
2. `related()` computes the similarity between the new story and existing stories using `similarity()`.
3. `similarity()` computes and returns a Python standard `float` value (`round(0.7 * tag_score + 0.3 * word_score, 4)`).
4. `item["similar"]` is populated with a dict containing `"score": <float>`.
5. When `table.put_item(Item=item)` is executed, `boto3`'s `TypeSerializer` validates the data types. DynamoDB does not support native Python `float` types and requires `decimal.Decimal` instead, raising `TypeError: Float types are not supported. Use Decimal types instead.`.
6. `handler()` catches the unhandled `TypeError` under `except Exception:`, logs `publish failed`, and returns HTTP status code 500.

## Fix
In `src/app.py`:
1. Imported `Decimal` from the standard `decimal` library.
2. In `similarity()`, converted the calculated float score to `Decimal(str(score))`.
3. Added unit tests in `tests/test_publish.py` covering publishing multiple stories and verifying that `app.publish` and `app.handler` succeed when similar stories are calculated and stored.
