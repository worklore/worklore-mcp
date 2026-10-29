# Second publish failure

`logs/error.log` shows `put_item` failing with `TypeError: Float types are not supported. Use Decimal types instead.` The first publish scans an empty table, so `similar` is empty. On the second publish, `related()` adds a similarity score. `similarity()` used Python division and float weights, producing a float nested in the item sent to DynamoDB.

`similarity()` now calculates and rounds with `Decimal` throughout, keeping the existing 0–1 score scale and four decimal places. A regression test publishes two stories through the handler using the DynamoDB-validating fake table, then checks that the second item contains the expected `Decimal` score. Run it with `python3 -m unittest discover tests`.

The colleague's note applies to the empty-table path hiding a float in a computed similarity score, DynamoDB's rejection of floats, and the need for a seeded second-write test. Its integer-percentage fix does not apply here: this service stores scores on a 0–1 scale to four decimal places, so `Decimal` preserves that format.
