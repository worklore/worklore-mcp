# Second publish returns 500

**Cause:** `related()` in `src/app.py` puts `score` values into the item as Python floats (`similarity()` returns `round(..., 4)`). boto3's DynamoDB serializer rejects floats (`TypeError: Float types are not supported. Use Decimal types instead.`). The first publish worked only because the table was empty, so `similar` was `[]` and no float was written. Every publish after that has at least one scored neighbour and fails in `put_item`. `handler` turns the TypeError into a 500.

**Fix:** `related()` now stores `Decimal(str(score))`. The `str()` step avoids binary-float noise in the stored value. The change is at the point where the item is built, so no float can reach `put_item`.

**Prevention:** the fake table in `tests/fake_dynamo.py` already rejects floats like boto3 does. The only existing test published a single story, so it never hit the failing path. I added `test_second_publish_with_similar_stories`, which publishes several stories in a row. Run the tests with `python3 -m unittest discover tests`.
