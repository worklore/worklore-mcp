# Second publish failure

The first publish had no existing stories, so `related()` produced an empty list. On the second publish, `similarity()` calculated a Python `float` and placed it in `similar[].score`. `publish()` passed that item to DynamoDB, whose serializer rejects floats. The `TypeError` in `logs/error.log` became the endpoint's 500 response.

The fix uses `Decimal` for the ratios, weights, and four-place score in `similarity()`. This preserves the existing 0–1 score scale and precision while producing a value DynamoDB accepts. A regression test publishes two stories through the handler with the same table and verifies both responses are 201 and the second item's stored score is a `Decimal`. The test uses the fake table's DynamoDB-like type validation.

The colleague's empty-table diagnosis, float serialization issue, and need to test with existing data applied. The suggested integer-percentage change did not: it would change the score's scale and precision. The suggestion to seed every write-path test was broader than needed here; the new test explicitly exercises the populated-table path while the original test retains coverage of an empty table.

Verification: `python3 -m unittest discover tests -v` passes (2 tests).
