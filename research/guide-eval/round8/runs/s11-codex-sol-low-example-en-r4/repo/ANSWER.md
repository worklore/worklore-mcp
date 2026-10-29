# Second publish failure

`related()` computed a similarity score as a Python `float` and placed it in the item sent to `table.put_item()`. Boto3's DynamoDB serializer rejects floats, producing the `TypeError` in `logs/error.log`. The first publish succeeded because the table was empty, so `similar` was an empty list and contained no score. Each later publish encountered an existing story and tried to store a float.

The fix converts each rounded score to `Decimal` before adding it to the stored item. `Decimal(str(score))` preserves the existing four-decimal score representation while giving DynamoDB a supported numeric type. A regression test publishes two stories to the validating fake table and checks the stored related score and both items. `python3 -m unittest discover tests` passes (2 tests).

The colleague's note applied to the empty-table versus populated-table path, DynamoDB's rejection of Python floats, and the need for a test with an existing record. Its integer-percentage fix did not apply: this service keeps fractional scores, so `Decimal` preserves their current meaning. No real-table publish was performed because the task is limited to the current directory and external publishing is prohibited.
