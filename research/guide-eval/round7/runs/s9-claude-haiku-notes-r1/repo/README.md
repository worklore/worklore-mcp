# storylib

The library behind the public story feed: publish a story, hide one (the
author withdraws it), list the feed. One DynamoDB table, key `slug`.

Layout:

- `src/app.py` -- `StoryLibrary`, the only module that talks to DynamoDB.
  The Lambda handlers (`api.py`, in the infra repo) call its methods; keep
  the method names and signatures stable.
- `tests/fake_dynamo.py` -- in-memory stand-in for the boto3 Table resource,
  so the tests run without AWS. It follows DynamoDB's expression rules
  (see its docstring).
- `tests/test_feed.py` -- the tests.
- `logs/` -- what came in this week: the production error on hide and a bug
  report from staging.

Run the tests (Python 3, no dependencies; on the servers `boto3` is
installed and `STORIES_TABLE` names the table):

    python3 -m unittest discover tests
