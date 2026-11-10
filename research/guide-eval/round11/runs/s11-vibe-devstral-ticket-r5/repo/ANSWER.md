# Cause and Fix

## Cause

The `similarity()` function in `src/app.py` returns a Python `float` (via `round(..., 4)`). When a second story is published, the `related()` function computes similarity scores between the incoming story and existing stories, and these float scores are stored in the `similar` list within the DynamoDB item. DynamoDB does not accept float types - it only accepts `int`, `str`, `bool`, `bytes`, `Decimal`, `None`, or collections thereof. This causes the `TypeError: Float types are not supported. Use Decimal types instead.` error on the second publish.

The first publish succeeds because the table is empty: `related()` returns an empty list, so no scores (and no floats) are written.

## Fix

1. **In `src/app.py`**: Import `Decimal` from the `decimal` module and change the `similarity()` function to return `Decimal(str(round(...)))` instead of a raw float. This converts the float to a string first (to avoid floating-point precision issues in Decimal constructor), then to a Decimal, which DynamoDB accepts.

2. **In `tests/test_publish.py`**: Seed the table with one story before testing the publish, so the test exercises the populated-table path where similarity scoring actually runs. This prevents the bug from being hidden by empty-table tests.

## Which parts of the colleague's note applied

The following parts of the colleague's note applied directly:

- "The API computed similarity scores between the incoming story and existing stories and stored the top matches." - **Applied**: Our code does exactly this via `related()` and `similarity()`.
- "The first publish succeeded because the table was empty: there were no matches, so there were no scores or floats to write." - **Applied**: This is the exact same scenario we have.
- "Once the table contained a story, the scoring path ran and passed Python floats to DynamoDB, which did not accept them." - **Applied**: This is the exact error we're seeing.
- "Divisions, averages and rounded scores feeding item dictionaries were places where computed floats could reach the write." - **Applied**: Our `similarity()` function uses division and `round()` to compute scores that go into the item dictionary.
- "I fixed it with a one-line change that made the scores integer percentages." - **Partially applied**: We used Decimal instead of integers, but the principle is the same - use a DynamoDB-compatible numeric type.
- "I also changed every write-path test to seed the table with one record before testing the write, so the populated-table path actually ran." - **Applied**: We updated the test to seed with one record.

The parts that did not apply:
- The specific mention of "integer percentages" - we used Decimal for precision, which is also acceptable to DynamoDB.
