# Why hiding crashes on prod and hidden stories stay in the staging feed

Both bugs have the same root cause. `hidden` is a **DynamoDB reserved word**,
and `src/app.py` wrote it as a bare attribute name in its expressions instead
of using a `#alias` through `ExpressionAttributeNames`. DynamoDB handles a bare
reserved word differently depending on the kind of expression, so the one
mistake produced two different symptoms.

## 1. Prod: Hide returns 500

`StoryLibrary.hide()` sent `UpdateExpression="SET hidden = :h, ..."`. When an
Update, Condition or Filter expression contains a bare reserved word, DynamoDB
rejects the call:
`ValidationException: Attribute name is a reserved keyword; reserved keyword: hidden`.
This is the error in `logs/prod-error.log`. The write never happened, so no
story could ever be hidden through the API.

## 2. Staging: a story hidden by hand still appears in the feed

Dasha's CLI command was correct: it used `#h` → `hidden`, and `get-item`
confirms the item has `hidden: true`. The problem is in the read path.
`StoryLibrary.feed()` scanned with
`ProjectionExpression="slug, title, hidden, published_at"`. When a
ProjectionExpression contains a bare reserved word, DynamoDB **does not
raise an error**. It just leaves that attribute out of every returned item.
So `hidden` was never in the scan results, `not i.get("hidden")` was always
true, and the feed filter let everything through. That's why there was no error and
no log line, and why neither a redeploy nor a private browser window helped.
There's no cache involved, and the feed reads from the correct table.

Bug 2 was hidden behind bug 1. Because Hide always failed, no story had ever
been hidden, so nobody noticed the feed filter didn't work. Fixing only the
crash would have made Hide return 200 while the story stayed in the public
feed.

## 3. Latent: `archive()` would crash the same way

`archive()` uses `ConditionExpression="status = :published"`, and `status` is
also reserved. It isn't wired to the API yet. It would have failed with the
same ValidationException as soon as the admin console started calling it.

## Fix

- `src/app.py`: every attribute name in every expression (publish, rename,
  hide, feed, archive) now goes through a `#alias`. A small `_names(...)`
  helper builds `ExpressionAttributeNames`. Method names and signatures are
  unchanged, so `api.py` needs no changes.
- `tests/test_feed.py`:
  - Regression tests for each cause:
    - hide works and removes the story from the feed;
    - a story hidden outside the library (like the CLI fix) is excluded from
      the feed;
    - hiding an unknown slug gives `ConditionalCheckFailedException`, not
      `ValidationException`;
    - archive works.
  - **Guard against it coming back:** the tests now run against `StrictTable`.
    It fails any call whose expression contains a bare attribute name, whether
    or not that name is reserved. The fake only knows a subset of DynamoDB's
    ~570 reserved words, so testing against that list alone would let the next
    one slip through. Requiring "always alias" doesn't depend on the list.

I checked this both ways. Run against the old `app.py` with the plain fake,
the new hide, feed, hide-unknown and archive tests fail with exactly the
production and staging symptoms. With the fix, all 9 tests pass
(`python3 -m unittest discover tests`).

## Unrelated, not changed

`feed()` makes a single `scan` and ignores `LastEvaluatedKey`. Once the table
is larger than 1 MB, the feed will silently miss stories. This deserves its
own fix (paginate, or use a GSI on `published_at`).
