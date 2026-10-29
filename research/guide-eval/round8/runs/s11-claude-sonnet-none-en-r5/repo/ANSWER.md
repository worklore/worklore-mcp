# Second publish returns 500

**Cause:** `related()` in `src/app.py` put `score` values into the item as Python floats (`similarity()` returns `round(..., 4)`). boto3's DynamoDB serializer rejects floats (`TypeError: Float types are not supported. Use Decimal types instead.`). The first publish worked only because the table was empty, so `similar` was `[]` and no float was written. From the second publish on, `similar` holds scored entries, so `put_item` fails and the handler returns 500.

**Fix:** `related()` now stores each score as `Decimal(str(score))`. `str()` avoids binary-float noise. I added a regression test (`test_second_publish_stores_similar_scores`) that publishes twice. The fake table rejects floats the way boto3 does, so the test fails on the old code.

**Not fixed:** `publish()` calls `scan` once and doesn't follow `LastEvaluatedKey`. Once the table passes 1 MB, `similar` will be computed from only part of the library. That is a separate problem.
