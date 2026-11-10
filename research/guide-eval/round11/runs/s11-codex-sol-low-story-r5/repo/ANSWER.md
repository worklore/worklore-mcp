# Second publish failure

The first publish stored an empty `similar` list because no stories existed yet. On the second publish, `related()` added a similarity score. `similarity()` calculated that score with Python float division and float weights; `table.put_item()` then passed the float to boto3, which rejected it (`TypeError: Float types are not supported. Use Decimal types instead.`). The handler turned that exception into HTTP 500.

`similarity()` now uses `Decimal` for both ratios and weights and rounds to four decimal places with `quantize()`. Every score in a stored `similar` entry is therefore compatible with DynamoDB. A regression test publishes two stories through the handler, checks that both return 201, and verifies that the second stored item contains a `Decimal` score. `python3 -m unittest discover tests -v` passes.

The colleague's note applies to the float rejection, the empty-table versus populated-table path, and the need for a test with an existing record. Its suggested integer-percentage fix was not used: keeping four-place `Decimal` scores preserves this service's score precision. The test uses the repository's DynamoDB-validating fake table; no real-table publish was run because the work is confined to this directory and external publishing is prohibited.
