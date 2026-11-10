**Cause**

The `related` function stored the raw similarity score (a Python `float`) in the
`similar` attribute of the DynamoDB item. DynamoDB rejects floats – it requires a
`Decimal` or an integer type. The first publish succeeded because the table was
empty, so no scores were written. On subsequent publishes a score was present and
the write failed with:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

**Fix**

Convert the similarity value to an integer percentage before storing it. The
updated `related` function multiplies the float (range 0‑1) by 100, rounds it, and
stores the resulting integer in the `score` field. This satisfies DynamoDB’s
type requirements while preserving the relative ordering of similarity scores.

**Applied notes from colleague**

- Identified that the bug only appears after the table contains a story (the
  empty‑table path hides the issue).
- Changed the write‑path to store integer percentages instead of floats.
 - Updated documentation/comments to explain the reasoning.

All tests now pass.

