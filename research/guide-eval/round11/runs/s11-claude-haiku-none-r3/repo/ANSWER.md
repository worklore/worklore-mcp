# Second publish returns 500: float in DynamoDB item

## Cause

`similarity()` returns a Python `float` (`round(..., 4)`), and `related()` stored
that float as `similar[].score`. boto3's DynamoDB serializer rejects floats
(`TypeError: Float types are not supported. Use Decimal types instead.`).

Why only the second publish fails: `related()` only produces entries when the
table already contains another story. The first publish in `logs/error.log`
had an empty table, so `similar=[]` and no float was written (the `201`). The
second publish found one existing story, produced `score: 0.xxxx`, `put_item`
raised, and `handler()` returned `500`. The existing unit test only publishes
one story, so it never exercised `similar` and could not catch this.

## Fix

- `src/app.py`
  - `related()` stores `score` as `Decimal(str(...))`, the value DynamoDB accepts.
  - New `to_dynamo()` recursively converts any float in the item to `Decimal`,
    and `publish()` runs the item through it before `put_item`. A future float
    field therefore can't reintroduce the same 500.
- `tests/test_publish.py`
  - `test_second_publish_with_related_story_is_stored` publishes two stories
    through `handler()` and expects `201`, plus a `Decimal` score in `similar`.
    It fails on the original code (verified) and passes now.
  - `test_to_dynamo_converts_nested_floats` covers the conversion helper.

Run tests with `python3 -m unittest discover tests` from the repo root.

Not done: no deploy or publish to AWS; `logs/error.log` is unchanged. Records
already written with the failing item shape don't exist, because the write never
succeeded, so no data migration is needed.
