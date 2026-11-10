# Second publish failure

The first publish had no existing stories, so `similar` was empty. On the second publish, `similarity()` calculated a Python `float` and `publish()` included it in `similar[].score`. DynamoDB rejects floats during `put_item`, causing the logged `TypeError` and the handler's 500 response.

`similarity()` now uses `Decimal` for ratios, weights, and the four-place score. Every stored related score, including zero, is a DynamoDB-supported `Decimal`. The regression tests publish twice through the handler against a table that rejects floats, and also cover a zero-similarity match. `python3 -m unittest discover tests -v` passes (3 tests).

The colleague's note correctly identified the empty-table trap, the float in the related-score write path, and the need for a populated-table regression test. Its integer-percentage fix did not apply: this service stores scores to four decimal places, so `Decimal` preserves that precision.
