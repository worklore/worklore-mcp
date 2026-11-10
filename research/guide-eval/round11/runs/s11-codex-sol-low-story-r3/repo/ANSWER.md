# Cause and fix

The first publish found no existing stories, so it stored an empty `similar` list. On the second publish, `related()` calculated a similarity score for the first story. `similarity()` returned a Python `float`, and `publish()` put that float inside the item sent to DynamoDB. The `TypeError: Float types are not supported. Use Decimal types instead.` in `logs/error.log` comes from boto3 serializing that item; the handler turned it into HTTP 500.

`similarity()` now returns a `Decimal` after rounding to the existing four decimal places. This preserves the score's value and makes nested `similar` entries valid for DynamoDB. A regression test publishes three stories through the handler into the validating fake table, checks the populated write succeeds, and verifies stored scores are `Decimal`. `python3 -m unittest discover tests` passes (2 tests). No external table was used.

The colleague's note applies to the state-dependent path, DynamoDB's rejection of floats, and the need to test a write after seeding data. Its integer-percentage fix was not used because it would reduce score precision and change the stored score scale. Its suggestion to publish twice against a real table was not used because this task is confined to the current directory and the fake table already checks the relevant boto3 type rule.
