# Hide crash on prod, hidden story still in the feed on staging

## Causes

Both symptoms are the same bug: `hidden` is a DynamoDB reserved word and
`src/app.py` used it as a bare attribute name in two different kinds of
expression.

1. **Prod crash (`logs/prod-error.log`).** `StoryLibrary.hide()` wrote
   `SET hidden = :h, ...` in an UpdateExpression with `hidden` bare. DynamoDB
   rejects that with `ValidationException: Attribute name is a reserved keyword;
   reserved keyword: hidden`. Loud, and the Hide button returns 500.

2. **Staging feed (`logs/bug-report.md`).** `StoryLibrary.feed()` asked for
   `ProjectionExpression="slug, title, hidden, published_at"`. A bare reserved
   word in a ProjectionExpression does not raise. The attribute is just absent
   from the returned item. So `not i.get("hidden")` never saw the flag, and
   every hidden story stayed in the public feed. Nothing was logged.

   Dasha's hand-hide was correct: she used `#h` for the name, so `hidden: true`
   is in the table. The write worked. The read side was the bug. The feed is
   not cached and does not read another table. It reads the same table and
   drops the field.

Reproduced locally against `tests/fake_dynamo.py` before the fix:
- `hide()` raises the same `ValidationException` as the prod log.
- The hand-hide write succeeds, then `feed()` still returns the story.
- `scan(ProjectionExpression="slug, hidden")` returns `[{'slug': 'a'}]`, with no
  error.

## Fix

- `src/app.py`: every attribute name in every expression is now a `#alias`,
  with an `ExpressionAttributeNames` entry. That covers `publish`, `rename`,
  `hide`, `feed` and `archive`, including names that are safe today.
- `archive()` had the same class of bug. `status` is in the
  ConditionExpression bare, and it is reserved. It is not wired to the API yet,
  so nothing has crashed, but it would have.
- Stopped the feed from relying on a silent projection: the projection now uses
  `#hidden`, with a comment saying why.

Tests (`tests/test_feed.py`, 11 total, all passing):
- `test_every_expression_uses_aliases`: static check. It parses `src/app.py` and
  fails on any bare attribute name in any `*Expression` string, reserved or
  not. This is the guard that stops the bug from coming back. It also catches
  the silent projection case, which no runtime error would report.
- `test_hide_then_feed_excludes_it`, and
  `test_feed_excludes_story_with_hidden_flag_set_by_hand`: the second writes the
  flag the way the CLI hand-fix did and asserts the feed drops the story. Those
  two are the "field actually set" tests the note asks for.
- `test_hide_records_who_and_when`, `test_archive_sets_archived_at`: cover the
  two paths that were broken.
- Test for the note's "verify" step, run directly: bare `hidden` in a
  ProjectionExpression returns `[{'slug': 'a'}]` with no error; `#hidden`
  returns the flag. Bare `status` in a ConditionExpression raises the
  ValidationException.

Against the original `src/app.py`, the new tests fail or error: the static guard,
the hand-hide feed test, the hide test, the hide-then-feed test, and archive.
Against the fix, all 11 pass.

Not done: no deploy, no change to staging or prod data. The staging story
`my-first-week` already has `hidden: true`, so it will leave the feed once the
fixed code is deployed, with no data fix needed. The hand-hide did not set
`hidden_by` or `hidden_at`, so that item lacks them. Backfilling those is a
data change on staging, so I left it for a decision.

## Colleague's note: what applied

- **Applied:** the DynamoDB reserved-word failure in an UpdateExpression is loud.
  The same failure in a ProjectionExpression is silent: the field comes back
  absent and the filter does nothing. Both were in this repo, and the
  second was the staging bug. (The note asks for the locations of its
  update_item, scan and query calls. Here they are all in `src/app.py`:
  update_item and scan, no query.)
- **Applied:** alias every attribute name in every expression, as a blanket
  convention and not a per-word check. Done in `src/app.py`, and enforced by
  the static test.
- **Applied:** the filter test must write the field and assert the filter
  excludes the record. The existing tests never set `hidden`, which is why
  nothing caught it.
- **Applied:** `status`, `date`, `name`, `type` are on the reserved list. In this
  repo `status` is the one in use (in `archive()`). The fake's `RESERVED` set
  has `status`, `name`, `type` and `date`. `title`, `slug` and `published_at`
  are not on that set, but are aliased anyway, per the blanket rule.
- **Did not apply:** the reproduction steps about `similar` and the
  "second write" crash. This repo has no `similar` field, and no second-write
  path. The note's `update_item`, `scan` and `query` locations also do not
  match: the repo has `update_item` and `scan` only, and `query` is not used.
- **Not verified here:** the note says DynamoDB keeps 573 reserved words. I have
  no access to the real list. The prod log confirms `hidden` is reserved on the
  real service. The `status` claim comes only from the note and the fake's
  subset, not from the real service. The blanket aliasing does not depend on
  either claim.
