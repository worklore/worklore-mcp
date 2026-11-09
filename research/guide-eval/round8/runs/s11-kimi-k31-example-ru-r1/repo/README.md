# stories-api

A small story library behind `POST /stories` (Lambda + DynamoDB table `stories`,
partition key `slug`). `src/app.py` is the whole service: `handler()` parses
the request and `publish()` stores the story together with its three most
similar existing stories (`similar: [{slug, score}]`, with `score` as an integer
percentage from 0 to 100), so the reader page can show "related" without a query
at read time. `logs/error.log` is the
production log from the first two publishes after the deploy.

Tests use an in-memory table (`tests/fake_dynamo.py`) that validates items the
way boto3 does, so no AWS account is needed. Run them with
`python3 -m unittest discover tests` from the repo root.
