# Why hide crashes on prod and why a hidden story stays in the staging feed

Both symptoms have the same root cause: `hidden` is a DynamoDB reserved word,
and `src/app.py` used it as a bare attribute name in expressions.

## Cause 1: hide returns 500 (logs/prod-error.log)

`StoryLibrary.hide` built the expression

    SET hidden = :h, hidden_by = :by, hidden_at = :t

DynamoDB rejects a reserved word used bare in an UpdateExpression, so
`UpdateItem` raised `ValidationException: Attribute name is a reserved keyword;
reserved keyword: hidden`. The exception was unhandled, so the API returned 500.
The story was never hidden.

## Cause 2: a hidden story stays in the feed (logs/bug-report.md)

`StoryLibrary.feed` scanned with

    ProjectionExpression="slug, title, hidden, published_at"

and then filtered out items with `i.get("hidden")`. A bare reserved word in a
ProjectionExpression does not raise an error. The attribute is silently left out
of the returned item. So `hidden` was always missing from the scan result, the
filter never removed anything, and the feed kept every story.

This is why the report looked like a cache problem. The hand-hide with
`--expression-attribute-names '{"#h":"hidden"}'` did write `hidden: true`
correctly, and `get-item` showed it. The feed call returned 200 with nothing in
the logs, because the feed code was working as written. It just never saw the
flag. The feed reads the table directly and has no cache. Whether staging's
`STORIES_TABLE` points at `stories-staging` is an environment setting I could
not check from this repo.

## Fix

- `src/app.py`: every attribute name in every expression is now a `#alias`
  with an `ExpressionAttributeNames` entry. This applies to `publish`, `rename`,
  `hide`, `feed` and `archive`. `archive` had the same bug with `status` (also
  reserved), so its condition would have failed too, though it is not wired to
  the API yet.
- `tests/test_feed.py` adds regression tests:
  - `test_hide_removes_story_from_feed`: hide works and the story leaves the feed.
  - `test_story_hidden_outside_the_library_leaves_feed`: a flag set with `#h`,
    the way the hand-hide did it, removes the story from the feed.
  - `test_archive_sets_archived_at`: archive works.
  - `test_every_expression_name_is_aliased`: parses `src/app.py` and fails if any
    attribute name in an `*Expression` string is bare. `tests/fake_dynamo.py`
    only knows a subset of DynamoDB's ~570 reserved words, so the fake alone
    would not catch every future case. This test checks the rule itself.

Before the fix, the three behavioural tests failed (two errors, one assertion
failure). After the fix, all 9 tests pass: `python3 -m unittest discover tests`.

## Staging data

No data migration is needed. The hand-hidden `my-first-week` item already has
`hidden: true`, so after deploying this fix it leaves the feed. Other stories were
never hidden on prod, because hide returned 500.

## Not changed, but noticed

- `feed()` makes one `scan` call and uses only the first page. DynamoDB returns
  at most 1 MB per page, and `LastEvaluatedKey` is ignored. This does not affect
  the reported bugs, but once the table is large enough the feed will silently
  miss stories.
- `hide` and `rename` use `attribute_exists(slug)`, so hiding a missing slug
  raises `ConditionalCheckFailedException`. The handler in `api.py` is in the
  infra repo, which I don't have, so I could not check whether it maps that to a
  404 or lets it 500.
