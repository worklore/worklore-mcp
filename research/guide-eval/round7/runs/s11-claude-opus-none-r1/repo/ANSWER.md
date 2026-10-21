# Why the second publish returns 500

## Cause

`publish()` stores each story with its top-3 related stories,
`similar: [{slug, score}]`. The score comes from `similarity()`, which returns a
Python **float** (`round(0.7 * tag_score + 0.3 * word_score, 4)`).

boto3's DynamoDB serializer does not accept floats. It raises
`TypeError: Float types are not supported. Use Decimal types instead.`
(see `logs/error.log`). `handler()` catches that as a generic exception and
returns 500.

The **first** publish worked only because the table was empty: `related()` had
nothing to compare against, so `similar` was `[]` and the item had no floats in it
(log: `similar=0 stored`). From the second publish on, there is at least one
existing story, so `similar` holds float scores and every `put_item` fails. It
also wasn't caught before production: the only test published a single story
into an empty table, so the float path never ran.

## Fix

- `src/app.py`: added `to_dynamo()`, which recursively replaces every float
  with `Decimal(str(f))`. `publish()` runs the whole item through it just
  before `put_item`. Because the conversion happens on the whole item at the one
  place it's written, a float added to the item later (a new score, ratio or
  weight) gets converted too, so this bug can't come back that way. Using `str()`
  keeps the short value (`0.35` → `Decimal('0.35')`, not
  `0.34999999999999997779…`).
- `tests/test_publish.py`: regression tests that
  - publish twice and check that the second item is stored with a `Decimal`
    score,
  - publish three stories through `handler()` and expect 201 each time,
  - check that `to_dynamo` converts nested floats.

  `FakeTable` rejects floats the same way boto3 does. The new tests fail on the
  old code (1 failure, 2 errors) and pass with the fix
  (`python3 -m unittest discover tests` → 4 tests OK).

Note: the stories already in production are fine. The first story has
`similar: []`, and the failed publishes wrote nothing. Stories published before
the fix won't list stories published after them as related, because `similar`
is computed only once, when a story is published. That's how the design already
works, not something this bug caused.
