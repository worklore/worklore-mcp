# Hide crash on prod and hidden stories in the staging feed

## Causes

Both bugs come from one thing: `hidden` is a DynamoDB reserved word, and the code
used it bare inside expressions.

1. **Prod crash (`logs/prod-error.log`).** `StoryLibrary.hide` built
   `UpdateExpression="SET hidden = :h, ..."`. DynamoDB rejects a bare reserved word
   in an update with `ValidationException: Attribute name is a reserved keyword`,
   so the handler returned 500 and nothing was written.

2. **Hidden story still in the feed (`logs/bug-report.md`).** This is not a cache and
   not a second table. The feed reads the same `stories` table. `StoryLibrary.feed`
   scanned with `ProjectionExpression="slug, title, hidden, published_at"`, and
   the bare `hidden` in a projection is not an error: DynamoDB silently leaves the
   attribute out of the returned item. So `i.get("hidden")` was always `None`, the
   filter `not i.get("hidden")` excluded nothing, and the feed returned 200 with
   the withdrawn story in it. The hand-run AWS CLI update was correct (it used
   `#h`), which is why `get-item` showed `hidden: true`. The data was right; the
   read path was the bug.

3. **Latent bug found while fixing.** `StoryLibrary.archive` has the same problem
   with `status` in its `ConditionExpression`. It is not wired to the API yet, so
   nothing hit it in production, but it would have raised the same error.

## Why the tests did not catch it

- No test called `hide()`, and the feed test never published a hidden story, so
  neither failure path ran.
- `tests/fake_dynamo.py` reproduces the real service faithfully on purpose: it
  raises for a bare reserved word in update, condition and filter expressions, and
  it drops it silently in projections. Nothing in the suite asserted anything about
  projections, so the silent case passed unnoticed.

## Fix

- `src/app.py`: every attribute name in every expression is now a `#alias` with an
  `ExpressionAttributeNames` entry (`publish`, `rename`, `hide`, `feed`, `archive`).
  This covers `hidden`, `status`, `title`, `slug`, and the rest, not just the words
  that failed, because DynamoDB's list is long and product field names will keep
  coming. A comment at the top of the methods states the rule.
- `tests/test_feed.py`:
  - `StrictTable` wraps the fake and fails the test on any bare reserved word in
    any expression, including projections. This turns the silent case into a
    failure, so the bug cannot come back unnoticed.
  - New tests: `hide` removes a story from the feed; `hide` records `hidden_by` and
    `hidden_at`; a story hidden by hand (the staging case, written with `#h`) leaves
    the feed; `archive` works.
  - Before the fix, 7 of 9 tests failed with the reserved-word errors. After the
    fix, all 9 pass (`python3 -m unittest discover tests`).

## Staging story

No data repair is needed. `my-first-week` already has `hidden: true`, so it will
drop out of `/feed` once the fixed code is deployed.

## Not verified

- Nothing was run against real DynamoDB or deployed. The reserved-word behaviour
  comes from the fake, which uses a subset of DynamoDB's list. The aliasing makes
  the code independent of that list, but it has not been checked on the real
  service.
- `api.py` lives in the infra repo and is not here, so the handlers were not
  checked. The public method names and signatures are unchanged, as the README asks.
- Nothing was committed.
