# Second publish failure

The first publish found an empty table, so `similar` was empty and the item contained no similarity score. On the second publish, `related()` computed a score with `/` and float weights. That Python `float` entered `similar` in the item passed to `put_item()`. Boto3's DynamoDB serializer rejects floats, as shown by the `TypeError` in `logs/error.log`, and the handler returned 500.

`similarity()` now performs its ratios, weighted sum, and four-place rounding with `Decimal`. The stored score remains a fractional value on the same 0–1 scale, but is a DynamoDB-supported type. A regression test publishes two stories through the handler against the validating fake table and checks the second item's stored score. The test suite passes with `python3 -m unittest discover tests`.

The colleague's note applied to the empty-table path hiding a float in a related-story write, and to testing with existing data. Its integer-percentage fix was not used: changing the score scale would change stored data semantics, while `Decimal` preserves them. This repository has no other scoring, deduplication, or aggregation write paths to change.
