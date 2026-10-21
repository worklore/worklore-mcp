# Why hiding a story broke, and the fix

## Causes

Both bugs come from the same thing. `hidden` is a DynamoDB reserved word, and
`src/app.py` used it as a bare attribute name in two expressions. DynamoDB
reacts differently depending on which expression it's in.

1. **Prod crash on Hide (`logs/prod-error.log`).** `StoryLibrary.hide` sent
   `UpdateExpression="SET hidden = :h, ..."`. If an UpdateExpression has a bare
   reserved word, DynamoDB rejects the whole call with
   `ValidationException: Attribute name is a reserved keyword; reserved keyword: hidden`.
   The handler doesn't catch it, so it returns a 500. Nothing gets written.

2. **Staging: a hand-hidden story still shows in the feed (`logs/bug-report.md`).**
   Dasha's CLI write did work, because she aliased the name (`#h`). The problem
   is on the read side. `StoryLibrary.feed` scans with
   `ProjectionExpression="slug, title, hidden, published_at"`. If a
   ProjectionExpression has a bare reserved word, DynamoDB doesn't raise an
   error. It just leaves that attribute out of every returned item. So
   `not i.get("hidden")` was always true, and the hidden filter never removed
   anything. This had nothing to do with caching or reading the wrong table.
   It also meant that fixing only the crash in (1) would still have left
   hidden stories in the feed.

3. **A third crash waiting to happen.** `archive()` uses
   `ConditionExpression="status = :published"`, and `status` is reserved too.
   It would have crashed the first time the admin console called it.

These bugs reached prod because the tests never hid a story, so there was no
test where the `hidden` field was actually set.

## Fix

- `src/app.py`: added `_names(*attrs)`. Every attribute name in every
  expression (put/update conditions, update SETs, the feed projection,
  archive's condition) now goes through a `#alias` plus
  `ExpressionAttributeNames`. This applies to names that aren't reserved
  today as well. Method names and signatures are unchanged.
- `feed()` now follows `LastEvaluatedKey`. A single scan page stops at 1 MB,
  so a large table would otherwise lose stories from the feed without any
  error. Nobody reported this; I fixed it while I was in the same method.
- `tests/test_feed.py`, new tests:
  - Hide through the library and check that the story leaves the feed and
    that `hidden_by` and `hidden_at` are stored.
  - Hide the way Dasha did (an aliased update made outside the library) and
    check that the story leaves the feed.
  - Hiding or archiving an unknown slug is rejected. Archiving a published
    story works.
  - The feed follows scan pages.
  - **Guard test (`NoBareAttributeNamesTests`):** runs every library
    operation against a recording table and fails if any Update, Condition,
    Filter, KeyCondition or Projection expression contains a bare attribute
    name, whether or not that name is reserved. This is what stops the bug
    from coming back. A new field can't be added bare, even with a name that
    isn't in the fake's partial reserved-word list.

`python3 -m unittest discover tests`: all 12 pass. Against the old `app.py`,
7 of the new tests fail.

Nothing was deployed. After this ships, the stories that people tried to hide
on prod (for example `why-i-left-mobx`) were never written as hidden, so they
need to be hidden again. Dasha's `my-first-week` on staging already has
`hidden: true`, so it will drop out of the feed as soon as the new build is
deployed.

## Which parts of the colleague's note applied

Applied:
- Both failure modes: the loud `ValidationException` on `hidden` in the
  UpdateExpression, and the silent missing field from the ProjectionExpression
  that turned the hidden filter into a no-op. Our case is the same as theirs.
- The rule to alias every attribute name in every expression instead of
  checking word by word. I did this, and it also covers `status` in
  `archive()`.
- Testing a filter with data where the field is actually set. That's the new
  hide tests.

Didn't apply, or adapted:
- `similar` and the earlier incidents in the note aren't in this codebase.
- The note suggests grepping for bare names. I used a guard test instead,
  because a grep only checks once and the test keeps checking in CI.
- The "Verify" step (use a reserved word bare on purpose against DynamoDB)
  wasn't run against AWS. The ground rules say no external services, and
  `tests/fake_dynamo.py` already models both behaviours.
- The "573 words" count isn't something I relied on. The fix doesn't depend
  on the list.
