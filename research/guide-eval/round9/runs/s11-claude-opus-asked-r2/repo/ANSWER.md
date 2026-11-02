# Why the second publish returns 500

## Cause

`publish()` saves each story along with its top-3 `similar` stories, and each
of those has a `score` from `similarity()`. That function returns
`round(0.7 * tag_score + 0.3 * word_score, 4)`, which is a Python **float**,
and boto3's DynamoDB serializer rejects floats:

    TypeError: Float types are not supported. Use Decimal types instead.

The first publish worked only because the table was empty. `related()` had
nothing to compare against, so `similar` was `[]`, the item held no floats and
`put_item` went through (log: `similar=0 stored`, then 201). From the second
publish on, the table holds a story, so a float score ends up in the item.
`put_item` then raises and `handler()` turns that into a 500. Every later
publish fails the same way.

The bug got past testing because the only test published into an empty table,
which is the one case where no scores are computed.

## Fix

- `src/app.py`: added `to_dynamo()`. It walks the whole item and turns every
  float into a `Decimal`, going through `str()` so `0.1` stays exactly `0.1`.
  `publish()` calls it on the complete item just before `put_item`. Because it
  runs on the whole item at the point of the write, a float in any field,
  current or added later, gets converted. The bug can't come back by someone
  adding another computed number.
- `tests/test_publish.py`: added tests that use a table that already has data:
  - publishing into a table that already has a story (checks the stored
    `similar` slug and that the score is a `Decimal`);
  - three publishes in a row through `handler()`, each expected to return 201;
  - a unit test of `to_dynamo()` on nested floats.

  Run against the original `app.py`, these tests fail with the same
  `TypeError` as the production log. With the fix, all 4 tests pass
  (`python3 -m unittest discover tests`).

Nothing was deployed. To confirm in production, publish two stories in a row
against the real table; the second write is the real test.
