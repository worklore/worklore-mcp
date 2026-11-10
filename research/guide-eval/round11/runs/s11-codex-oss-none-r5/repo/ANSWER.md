**Cause**

The `similarity` function returned a plain Python ``float``. When the story
item was written to DynamoDB, the AWS SDK attempted to serialize that value as a
`Number` attribute. DynamoDB does not accept native floating‑point values – it
requires numbers to be represented as ``Decimal`` instances. The second publish
therefore raised:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

**Fix**

* Import ``Decimal`` from the ``decimal`` module.
* After computing the similarity score, convert the rounded float to a
  ``Decimal`` via ``Decimal(str(raw))``. This preserves the exact decimal value
  and satisfies DynamoDB's type requirements.
* Updated the module docstring and added a brief comment explaining the change.

The modification is isolated to `src/app.py` and does not affect other logic.

Running the test suite again passes, and publishing the same story twice no
longer triggers a 500 error.
