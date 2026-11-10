# Why the second publish returns 500

## Cause

`similarity()` in `src/app.py` returns `round(..., 4)`, which is a Python `float`.
`related()` puts that float in each `similar` entry (`{"slug", "score"}`), and
`publish()` passes the whole item to `table.put_item`. boto3 rejects floats:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The first publish works only because the table is empty. `related()` has no
existing stories to score, so `similar` is `[]` and no float is written
(`similar=0 stored` in the log at 09:14:02). The second publish finds one story,
produces a float score, and `put_item` raises. `handler()` catches that and
returns 500. The failed write stores nothing, so no bad item is left behind.

The bug is state-dependent: it exists only once the table has data. The existing
tests only ever published into an empty `FakeTable`, so they never reached it.

## Fix

- **`src/app.py`**: added `to_dynamo()`, which recursively converts floats to
  `Decimal(str(value))`. `publish()` now calls `table.put_item(Item=to_dynamo(item))`.
  The conversion happens at the write boundary, so scores can stay floats for
  sorting. Any float added later is converted too, not just `similar[].score`.
  I used `Decimal` rather than the integer-percentage change in the colleague's
  note, because it keeps the score's value and precision.
- **`tests/test_publish.py`**: three new tests.
  - `test_second_publish_into_populated_table` seeds one story, publishes a second,
    and checks that the stored score is a `Decimal` and points at the seed story.
  - `test_handler_second_publish_returns_201` reproduces the 500 at the handler.
  - `test_to_dynamo_converts_nested_floats` covers the converter.

Before the fix, the handler test returned `500 != 201` and the populated-table
test failed with the float `TypeError`. After the fix, all 4 tests pass:

```
python3 -m unittest discover tests -v   # 4 tests, OK
```

## Colleague's note: what applied

- **Applied:** the diagnosis (computed float written to DynamoDB; the first write
  passes only because the table is empty) and the seeded-table test. Both match
  this code.
- **Applied:** the grep step. The only `/` and `round()` in `src/app.py` are the
  Jaccard ratios and the final `round` in `similarity()`. Only the rounded score
  reaches a DynamoDB write, and the converter now covers it.
- **Adapted:** "convert at the boundary." The note suggests ints or `Decimal`. I
  used `Decimal` to keep the existing score values, not integer percentages.
- **Not applied:** the "publish twice against a real table" step. This sandbox has
  no AWS access, and you asked me not to deploy or publish. Run it yourself after
  you deploy. The fake table in `tests/fake_dynamo.py` already rejects floats the
  way boto3 does, so the regression tests are a reasonable stand-in, but not a
  substitute for a real table.

## Could it come back?

Three guards:

1. `to_dynamo()` runs on every write, so a new float field cannot reach boto3
   unconverted.
2. The populated-table test fails if the first and second publish paths diverge.
3. `FakeTable` still rejects raw floats, so a write that skips `to_dynamo()` fails
   in tests.

## Not addressed

- `publish()` calls `table.scan(...)` once and does not follow `LastEvaluatedKey`.
  Once the library exceeds one scan page (1 MB), `related()` will only see part of
  the library, so the "top 3 similar" will quietly be wrong. This is a separate
  issue and I did not change it.
- The `FakeTable.scan` accepts `**kwargs` and ignores `TableName`, so the tests
  do not check how the real call is shaped.
