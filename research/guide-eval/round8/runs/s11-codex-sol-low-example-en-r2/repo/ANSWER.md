# Second publish failure

`logs/error.log` shows boto3 rejecting a Python `float` in `table.put_item`: `Float types are not supported. Use Decimal types instead.` The float came from `similarity()`. On the first publish, the table is empty, so `related()` produces no scores and the write succeeds. On the second publish, an existing story produces a score inside `similar`, and DynamoDB serialization fails. The handler turns that exception into HTTP 500.

`similarity()` now computes and rounds scores with `Decimal` throughout, preserving the existing four decimal place score scale while making the stored value valid for DynamoDB. A regression test sends two requests through the handler using the validating fake table, then checks that the second item has a `Decimal` related score. `python3 -m unittest discover tests -v` passes (2 tests).

The colleague's note applied to the float rejection, the empty-table versus populated-table path, and the need for a seeded second-write test. Its proposed integer percentage conversion was unnecessary here because `Decimal` retains the existing score precision. A real DynamoDB publish was not run; verification used the local fake table, which rejects floats like boto3.
