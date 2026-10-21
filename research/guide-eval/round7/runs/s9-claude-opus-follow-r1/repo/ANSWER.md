# Why hiding a story broke, and why hidden stories stayed in the feed

Both bugs come from the same thing. `hidden` is a DynamoDB reserved word, and
`src/app.py` used it as a bare attribute name in two expressions.

## 1. Prod: `hide()` crashes (logs/prod-error.log)

`StoryLibrary.hide` sent `UpdateExpression="SET hidden = :h, ..."`. DynamoDB
rejects reserved words used bare in an UpdateExpression, so it raised
`ValidationException: Attribute name is a reserved keyword; reserved keyword: hidden`.
That error is unhandled in `api.hide_story`, so the user gets a 500. No story
could ever be hidden through the API.

## 2. Staging: a story hidden by hand still shows in the feed (logs/bug-report.md)

The hand-written CLI update used `#h` → `hidden`, so the flag really was
written (`get-item` shows it). The problem is on the read side. `feed()`
scanned with `ProjectionExpression="slug, title, hidden, published_at"`, with
`hidden` bare. With a bare reserved word in a projection, the field is left
out of the returned items and no error is raised. That is how the in-repo
fake behaves (`tests/fake_dynamo.py`), and it matches the report: 200
response, nothing in the logs. So `not i.get("hidden")` was always true and
the filter never removed anything. It wasn't caching and it wasn't the wrong
table.

Caveat: AWS's own documentation says a reserved word in a ProjectionExpression
is also rejected with a ValidationException. If staging behaved that way,
`/feed` would return 500, not 200. The cause in the code is the same either
way, and so is the fix.

The existing tests didn't catch either bug. No test ever called `hide()`, and
no test put a story in the table with `hidden` set, so the filter only ever
saw items where the field was missing anyway.

## Other problems found and fixed

- `archive()` used `ConditionExpression="status = :published"`. `status` is
  reserved, so it would have crashed the same way the first time the admin
  console called it.
- `feed()` made a single `scan` call. DynamoDB returns at most 1 MB per scan
  call, so once the table grows, stories after the first page would silently
  disappear from the feed. It now follows `LastEvaluatedKey`.

## Fix (so it can't come back)

- `src/app.py`: every attribute name in every expression (update, condition,
  projection) now goes through a `#alias` in `ExpressionAttributeNames`. This
  applies to every name, reserved or not, and is documented on the class.
  Method names and signatures are unchanged.
- `tests/test_feed.py`:
  - All library tests now run against `AliasOnlyTable`. It rejects any bare
    attribute name in any expression, so a new field can't slip in un-aliased,
    whether or not it's on today's reserved list.
  - New tests write data with the field actually set: hide via `hide()`, hide
    by hand the way staging did, hide an unknown slug, archive, and feed
    pagination.
  - Two tests pin the fake's two reserved-word behaviours (a loud error in an
    update, a silently dropped field in a projection).
  - Against the old `app.py`, the new tests reproduce both reported failures:
    the `hidden` ValidationException, and the hand-hidden story still in the
    feed.

Run: `python3 -m unittest discover tests`. All 12 tests pass.
