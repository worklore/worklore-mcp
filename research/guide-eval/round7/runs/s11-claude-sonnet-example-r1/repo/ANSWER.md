# Why the second publish returns 500

**Cause:** `similarity()` in `src/app.py` returned `round(..., 4)`, a Python `float`. `publish()` stores the top-3 matches (`similar: [{slug, score}]`) in the item. On the first publish the table is empty, so `related()` returns `[]` and no floats exist. On the second publish there is an existing story, so a float `score` goes into the item, and boto3 raises `TypeError: Float types are not supported. Use Decimal types instead.` at `put_item`. `handler()` turns that into a 500 (see `logs/error.log`). The only test published to an empty table, so it never ran this path.

**Fix:**
- `similarity()` now returns an integer percentage (0-100), which DynamoDB accepts.
- Added tests in `tests/test_publish.py` that publish onto a populated table, so the similarity path runs. The fake table rejects floats the way boto3 does. They also check the score is an `int` and that re-publishing the same slug works.
- `python3 -m unittest discover tests` passes.

**Colleague's note:** it was the same bug, and I used these parts:
- The diagnosis: floats appear only once existing data is scored.
- The int-percentage fix.
- Seeding the table before testing a write.

I did not use the real-table double-publish check. I can't deploy or call AWS here, so the fake table stands in for it. The grep for `round(` and `/` found only `similarity()`.

**Caveat:** the `score` format changes from a 0-1 float to a 0-100 int. Nothing has been stored yet, because every publish after the first one failed. Anything that reads `score` should expect the new scale.
