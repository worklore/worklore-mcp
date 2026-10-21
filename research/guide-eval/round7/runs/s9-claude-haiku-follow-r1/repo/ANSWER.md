# Hiding a story: two causes, one word

Both bugs come from the same word, `hidden`, which is on DynamoDB's
reserved-word list. It fails in two different ways depending on which
expression it appears in.

## 1. Prod crash on Hide: bare `hidden` in an UpdateExpression

`StoryLibrary.hide()` ran:

    SET hidden = :h, hidden_by = :by, hidden_at = :t

DynamoDB rejects a reserved word used bare in an UpdateExpression, so every
call raised `ValidationException: Invalid UpdateExpression: Attribute name is
a reserved keyword; reserved keyword: hidden` and the handler returned 500.
That is what `logs/prod-error.log` shows.

## 2. Staging: hidden stories stay in the feed (a silent no-op)

`StoryLibrary.feed()` scanned with:

    ProjectionExpression="slug, title, hidden, published_at"

A reserved word in a ProjectionExpression does not raise. DynamoDB just omits
the attribute from every returned item. The feed then filtered on
`not i.get("hidden")`, which always saw `None`, so nothing was ever excluded.
The scan returned 200 and nothing was logged.

The hand-hidden item in `logs/bug-report.md` is correct in the table:
the AWS CLI command used the `#h` alias, so `hidden: true` was written. The
read path was the broken half. So the answer to Dasha's question is no: the
feed is not cached, and it reads the same table, `stories-staging`. Its
projection was dropping the flag.

## 3. Latent: `archive()` had the same problem

`archive()` used bare `status` in a ConditionExpression. `status` is also on
the reserved list, so `archive()` would hit the same ValidationException as
cause 1 once it is wired up. It is not called from the API yet, so nothing
broke in production.

## The fix

- Every attribute name in every expression in `src/app.py` is now an alias
  (`#hidden`, `#slug`, `#status`, ...) with an `ExpressionAttributeNames`
  entry, including names that are not known to be reserved. The list is long
  and product needs choose field names, so the rule is blanket, not per word.
- `tests/fake_dynamo.py`: `FakeTable` now raises on a bare reserved word in a
  ProjectionExpression by default (`strict_projection=True`). The real service
  is silent here, and that silence is what made cause 2 hard to see. Pass
  `strict_projection=False` to reproduce the real behaviour.
- `tests/test_feed.py`: new tests for `hide()` (the flag is written, the
  error case for an unknown slug, a hidden story leaves the feed, and the
  other stories stay), `archive()`, and the strict projection guard. The
  hidden-story test sets the flag on the record the feed reads, so the filter
  is really exercised.

The `fake_dynamo` reserved list is a subset of the real one (the README says
~570 words). The tests therefore cannot prove a name is safe. Aliasing every
name is the real protection; the tests check that the aliases are used.

## Verification

    python3 -m unittest discover tests   # 10 tests, all pass

Before the fix, 5 of the new tests failed or errored, including the
hidden-story-leaves-the-feed test. After the fix, all pass.

Manual check of the two failure modes, using the non-strict fake:

- Bare `hidden` in an UpdateExpression: `ValidationException`, as in prod.
- Bare `hidden` in a ProjectionExpression: returns `[{'slug': 'a'}]`, with no
  error and no `hidden` key. This is the silent failure.

## Not done

- Nothing was deployed or sent anywhere. The staging feed and prod Hide
  should be re-checked after a deploy of this change.
- The changes are uncommitted in the working tree.
