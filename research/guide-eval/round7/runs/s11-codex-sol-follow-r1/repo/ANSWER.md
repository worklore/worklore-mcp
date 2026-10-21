# Second publish failure

The first publish found no existing stories, so `similar` was empty. On the second publish, `similarity()` calculated a Python float and `related()` placed it in `similar[0].score`. `put_item` then failed while serializing the item because DynamoDB does not accept Python floats. The exception became the HTTP 500 shown in `logs/error.log`.

`similarity()` now returns a rounded integer percentage (0–100), so computed scores are valid DynamoDB numbers. A regression test publishes two stories through the handler using the validating in-memory table, checks that both requests return 201, and verifies that the second item stores the expected integer score (65). This covers the populated-table path that the original first-publish test missed.

Verification: `python3 -m unittest discover tests` passes (2 tests). No external table was used because this task is confined to the current directory.
