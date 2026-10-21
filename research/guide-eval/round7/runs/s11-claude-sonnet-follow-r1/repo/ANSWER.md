# Why the second publish returns 500

**Cause:** `similarity()` in `src/app.py` returned a Python float (`round(0.7*tag + 0.3*word, 4)`).
`publish()` stores the top-3 matches as `item["similar"]`, each with that float `score`.
boto3's DynamoDB serializer rejects floats (`TypeError: Float types are not supported. Use Decimal types instead.`).
On the first publish the table is empty, so `related()` returns `[]`: no scores, no floats, no error.
From the second publish on, scores exist and `put_item` fails (see `logs/error.log`). The bug only exists once there is data.

**Fix:**
- `similarity()` now returns an integer percentage (0-100), so nothing float-valued reaches `put_item`.
- Tests: `test_second_publish_with_existing_records` and `test_handler_twice_returns_201` seed a record and then write a second one. That runs the populated-table path, and the fake table rejects floats the way real DynamoDB does. They fail on the old code and pass now.

**Prevention:** every write-path test must seed the table first. The empty-table path happens once in production. Convert computed values (divisions, `round()`) to int or `Decimal` where they enter the item.

Not verified against a real table (no deploy allowed here). Only the fake table was used.
