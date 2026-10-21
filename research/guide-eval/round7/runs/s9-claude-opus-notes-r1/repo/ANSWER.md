# Why hiding a story broke

Both bugs come from the same source: **`hidden` is a DynamoDB reserved word**,
and `src/app.py` used it bare (unaliased) in two expressions. The two
expressions fail in different ways.

## 1. Prod: Hide returns 500 (`logs/prod-error.log`)

`StoryLibrary.hide()` sent

    UpdateExpression="SET hidden = :h, hidden_by = :by, hidden_at = :t"

DynamoDB rejects a bare reserved word in an UpdateExpression:
`ValidationException: Invalid UpdateExpression: Attribute name is a reserved
keyword; reserved keyword: hidden`. Nothing caught it, so every Hide call
returned a 500 and no story was ever hidden through the app. (`hidden_by` and
`hidden_at` are not reserved. Only `hidden` triggers the error.)

## 2. Staging: a hand-hidden story stays in the feed (`logs/bug-report.md`)

The CLI write was correct (it aliased `#h`), and the item really has
`hidden: true`. The feed is not cached, and it reads the right table. The
problem is that `StoryLibrary.feed()` scanned with

    ProjectionExpression="slug, title, hidden, published_at"

The bare `hidden` in the projection does not raise an error. The attribute is
just left out of every returned item. `not i.get("hidden")` then sees `None`
for every story, so the "exclude hidden" filter never excludes anything. The
call returns 200 and nothing is logged, which matches what Dasha saw. This is
the silent version of bug 1. It stayed unnoticed because the Hide button
crashed first, so no story could reach the feed with `hidden` set.

(This is how the in-repo test double, `tests/fake_dynamo.py`, models the
projection case, and it matches the staging symptoms. I'm not sure it matches
AWS, though: as far as I know, AWS documents a bare reserved word in a
ProjectionExpression as a ValidationException. If that's what staging does,
the 200 must come from some other layer that hides the error, and that's
worth checking in `api.py`. Either way, the fix below removes bare names from
the projection.)

## Why the tests missed it

- No test called `hide()` at all, and no test checked the feed with a story
  where `hidden` is actually set.
- The fake table only knows a subset of DynamoDB's ~570 reserved words. Even
  with more tests, a new field name that isn't in that subset would get past
  the fake and fail on AWS.

## The fix

- **`src/app.py`**: every attribute name in every expression now goes through
  a `#alias` with `ExpressionAttributeNames`, built by a small `_names()`
  helper. That covers `hide`, `feed`, `publish`, `rename` and `archive`. The
  rule is "alias always", not "alias the words on the list". The list is long
  and full of ordinary words (`status`, `name`, `date`, `type`, ...), and
  future field names won't be picked with it in mind.
  - The same latent bug was waiting in `archive()`, which isn't wired to the
    API yet: `ConditionExpression="status = :published"` (`status` is
    reserved). It would have crashed the first time the admin console
    called it. Fixed the same way.
  - `feed()` now follows `LastEvaluatedKey`. Before, it read only the first
    1 MB scan page, so on a bigger table some stories (including hidden
    flags) would never have been seen.
  - Method names and signatures are unchanged, so `api.py` doesn't need to
    change.
- **`tests/test_feed.py`**:
  - `AliasOnlyTable` wraps the fake and fails any call that has a bare
    attribute name in any expression. This enforces the convention itself,
    so a new field can't slip through whether or not the fake knows it's
    reserved. All tests use it.
  - New tests: hiding removes a story from the feed and records
    `hidden_by`/`hidden_at`; a story hidden outside the app (the staging
    case) is excluded; hiding an unknown slug is rejected; `archive()` works;
    the feed reads every scan page.
  - Against the old `src/app.py`, all 10 tests fail. Against the fix, all
    pass (`python3 -m unittest discover tests`).

## After deploying

- Retry hiding `why-i-left-mobx` on prod. Its two earlier attempts failed and
  changed nothing.
- On staging, `my-first-week` should leave the feed as soon as the new build
  is live. No data fix is needed.
