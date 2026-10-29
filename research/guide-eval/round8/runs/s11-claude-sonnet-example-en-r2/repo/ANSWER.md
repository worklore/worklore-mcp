# Why the second publish returns 500

**Cause:** `similarity()` in `src/app.py` returns a float (`round(0.7*... , 4)`), and `related()` stores it as `similar[].score` in the item. boto3 refuses floats for DynamoDB (`TypeError: Float types are not supported`, see logs/error.log, raised at `table.put_item`). The first publish hits an empty table, so `related()` returns `[]` and no float exists; from the second publish on there are scores, so it fails.

**Fix:** added `to_dynamo()` (recursive float -> `Decimal(str(x))`) and apply it to the item right before `put_item`, so any float, now or added later, is converted at the write boundary. Added a regression test that publishes a second and third story into a populated table (`tests/test_publish.py`); the fake table rejects floats like boto3 does, so the test fails without the fix.

**Colleague's note:** applied — the diagnosis (floats only appear once data exists), converting at the boundary, and seeding the table in the write-path test. Not applied — switching scores to integer percentages (kept fractional scores as Decimal so the stored data is unchanged), and the real-table double publish (no external access allowed here).

Side note, not changed: `publish` uses a single unpaginated `scan`, which will miss stories once the table exceeds 1 MB.
