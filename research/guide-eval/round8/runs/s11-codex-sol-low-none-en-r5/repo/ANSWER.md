# Second publish failure

The first publish finds no existing stories, so `similar` is empty. On the second publish, `similarity()` produces a Python `float` and `related()` puts it in `similar[0].score`. The DynamoDB resource serializer rejects floats, including floats nested inside an item, so `put_item()` raises `TypeError` and the handler returns 500.

`related()` now converts each computed score to `Decimal` before it enters the stored item. It converts through `str()` to preserve the rounded decimal value instead of capturing the float's binary approximation. A regression test publishes two stories through the handler, checks both return 201, and verifies that the stored score is a `Decimal`.

Verification: `python3 -m unittest discover tests` passes (2 tests).
