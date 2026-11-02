# Why the second publish returns 500

## Cause

`publish()` stores each story with its most similar existing stories:
`similar: [{slug, score}]`. `similarity()` returns a Python `float`
(`round(0.7 * tag_score + 0.3 * word_score, 4)`).

- **First publish:** the table is empty, so `related()` returns `[]`. No float
  ends up in the item and `put_item` works (201).
- **Every publish after that:** at least one story already exists, so
  `similar` holds a `float` score. boto3's DynamoDB serializer rejects floats
  (`TypeError: Float types are not supported. Use Decimal types instead.`).
  `handler()` catches that as a generic `Exception`, so the request returns 500.
  That matches `logs/error.log` exactly: 201 once, then 500 at `app.py:63`
  (`table.put_item`).

The existing test missed it because it publishes only one story into an empty
table, which never builds a non-empty `similar` list.

## Fix

- `src/app.py`: added `to_dynamo()`, which walks the item and turns every
  `float` into a `Decimal` (through `str()`, so `0.4567` stays `Decimal('0.4567')`
  instead of picking up binary noise). `publish()` runs every item through it
  just before `put_item`. Because the conversion happens at the storage
  boundary, not only on `score`, a float field added later (a new metric,
  a different scoring formula) is converted too, instead of failing in
  production again.
- `tests/test_publish.py`: regression tests that
  - publish two related stories and check that both are stored and the
    neighbour's score is a positive `Decimal`;
  - send two publishes through `handler()` and expect 201 both times;
  - unit-test `to_dynamo()` on nested floats, and check that ints and bools
    are left alone.

  The fake table already rejects floats the same way boto3 does, so these
  tests fail on the old code (verified: 1 failure and 2 errors) and pass with
  the fix (`python3 -m unittest discover tests` → 4 OK).

## Related, not changed

- `table.scan()` reads only the first 1 MB page (it ignores `LastEvaluatedKey`),
  and it does a full scan on every publish. Once the library grows, `similar`
  will quietly miss stories and publishing will slow down.
- An API key appears in plain text in `README.md`, and an API token in
  plain text in `samconfig.toml`. Both files are committed. Consider rotating
  them and moving them to a secret store.
