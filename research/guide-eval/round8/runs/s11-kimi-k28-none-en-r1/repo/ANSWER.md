# Why the second publish returned 500

## Cause

`similarity()` in `src/app.py` returned a Python `float`
(`round(0.7 * tag_score + 0.3 * word_score, 4)`), and `related()` stored that
float as `score` inside each entry of the item's `similar` list. boto3's
DynamoDB serializer rejects floats (`TypeError: Float types are not supported.
Use Decimal types instead.`), so `table.put_item(...)` blew up.

The bug was invisible on the first publish after deploy: the library was
empty, `scan()` returned no items, `similar` came out as `[]`, and no float
ever reached `put_item` — hence the log line `similar=0 stored` and a 201.
From the second publish on, the table contained at least one story, `similar`
was non-empty, every entry carried a float `score`, and every request 500'd.
That's why it "worked once" and then never again.

## Fix (in `src/app.py`)

1. `similarity()` now returns `Decimal(str(round(...)))` — the score is a
   Decimal at the source, with `str()` avoiding binary-float artifacts.
2. Defense in depth: `publish()` passes the whole item through a new
   `_decimalize()` helper that recursively converts any float to `Decimal`
   before `put_item`. Even if a future change introduces another float
   somewhere in the item, it can never reach DynamoDB and cause this again.

Regression coverage: `tests/test_publish.py` gained
`test_second_publish_stores_similar_as_decimal`, which publishes two stories
(the exact failing scenario) and asserts the stored score is a `Decimal`. The
old test only published once, which is why the bug slipped through. All tests
pass: `python3 -m unittest discover tests`.
