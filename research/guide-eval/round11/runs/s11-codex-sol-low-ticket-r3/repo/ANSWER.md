# Second publish failure

The first publish stored `similar: []` because the table was empty. On the second publish, `related()` called `similarity()` for the existing story. Its division and weighted average produced a Python `float`, which entered `similar[0].score`. DynamoDB rejects floats during `put_item`, producing the logged `TypeError` and the HTTP 500.

`similarity()` now uses `Decimal` for the ratios, weights, and four-place rounding. The stored score keeps its original 0–1 scale and precision, and DynamoDB accepts it. A regression test publishes two stories through the handler using the validating fake table, checks both 201 responses, and checks the stored related score. `python3 -m unittest discover tests -v` passes (2 tests).

The colleague's note applies to the float rejection, the empty-table path hiding the bug, and the need to test a write with existing data. Its integer-percentage fix does not apply here: this API stores similarity as a 0–1 score to four decimal places, so changing it to an integer percentage would change the stored value's meaning and precision. The suggestion to seed every write-path test is broader than this codebase needs; the new test explicitly exercises the populated-table path.
