# Cause

`similarity()` in `src/app.py` used division and returned `round(...)` with a precision argument, which is a Python `float`. `publish()` placed that value in `similar[].score`, and DynamoDB's boto3 serializer rejects floats with `TypeError: Float types are not supported. Use Decimal types instead.`

The first publish succeeded because the table was empty, so `related()` returned an empty list and no float reached `put_item`. The second publish found an existing story, computed a float score, and failed; `handler()` converted that exception into the observed 500 response. The original test only exercised the empty-table path.

# Fix

- `src/app.py` now returns similarity as a whole-number integer percentage from 0 to 100. DynamoDB accepts Python integers, and the relative ordering of scores is unchanged.
- `tests/test_publish.py` now includes a regression test that seeds the table before publishing. It exercises the populated-table path and verifies the stored related-story score is the integer `100`, so reintroducing a float will fail the test.

Verification: `python3 -m unittest discover tests` passes both tests. Calling the real `handler()` twice locally also returns 201 for both requests, with an integer similarity score stored for the second story.

# Colleague's note

Applied: the float-at-the-DynamoDB-boundary diagnosis, the explanation for why only the second write fails, conversion to integer percentages, and adding a seeded-table write test.

Not applied: converting scores to `Decimal` was unnecessary because the integer representation is sufficient. No real AWS table or deployment was used; the existing fake table reproduces boto3's type validation locally.
