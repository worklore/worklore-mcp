# Why the second publish returns 500

**Cause.** `publish()` stores the story together with `similar: [{slug, score}]`.
The first story is published into an empty library, so `similar` is `[]` and the
write succeeds (201). From the second story on, `related()` returns `score`
values computed by `similarity()` as Python `float`. boto3's DynamoDB serializer
rejects floats (`TypeError: Float types are not supported. Use Decimal types
instead.`), which `handler()` turns into a 500. The test only published one
story, so it never hit this path.

**Fix.** `similarity()` now returns `Decimal(str(round(..., 4)))`, so every
score is a DynamoDB-compatible number (via `str`, to avoid binary-float
noise). Added `test_second_publish_with_similar_stories`, which publishes two
stories; the fake table rejects floats the same way boto3 does, so any float
reintroduced into the item fails the test.
