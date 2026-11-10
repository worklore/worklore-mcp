# Second publish failure

`logs/error.log` shows DynamoDB rejecting a Python `float` during `put_item`. The first publish scanned an empty table, so `related()` returned an empty list and the item contained no score. On the second publish, `similarity()` calculated a float and placed it in `similar[0].score`; DynamoDB's serializer raised `TypeError: Float types are not supported. Use Decimal types instead`, which the handler returned as HTTP 500.

`similarity()` now calculates and rounds scores with `Decimal` throughout, preserving the existing four-decimal score scale while producing a DynamoDB-compatible value. A regression test publishes two stories through the handler, checks both HTTP responses, and verifies the stored related score is a `Decimal`. The test suite passes with `python3 -m unittest discover tests -v`.

The colleague's diagnosis of the empty-table versus populated-table path, nested similarity score, DynamoDB float rejection, and missing populated-table test all applied. The proposed integer-percentage fix did not apply: it would change the existing 0–1 score scale and discard its four-decimal precision. The note's broader references to deduplication and aggregation did not apply to this service; its only computed write-path score is in `related()`.
