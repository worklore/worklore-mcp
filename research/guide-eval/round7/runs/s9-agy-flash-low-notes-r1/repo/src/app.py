"""storylib - the story library behind the public feed.

Three operations: publish a story, hide one (the author withdraws it) and
list the public feed. Storage is a single DynamoDB table keyed by `slug`.
This module only talks to a boto3 Table resource; the tests hand it
tests/fake_dynamo.FakeTable instead, and the HTTP handlers (api.py, in the
infra repo) hand it dynamo_table().
"""
import os
import time


def dynamo_table():
    """The real table. boto3 is only installed on the servers."""
    import boto3
    return boto3.resource("dynamodb").Table(os.environ.get("STORIES_TABLE", "stories"))


class StoryLibrary:
    FEED_LIMIT = 50

    def __init__(self, table, clock=time.time):
        self.table = table
        self.clock = clock

    def publish(self, slug, title, body, author):
        """Create a story. Refuses to overwrite an existing slug."""
        self.table.put_item(
            Item={
                "slug": slug,
                "title": title,
                "body": body,
                "author": author,
                "published_at": int(self.clock()),
                "status": "published",
            },
            ConditionExpression="attribute_not_exists(#s)",
            ExpressionAttributeNames={"#s": "slug"},
        )

    def get(self, slug):
        return self.table.get_item(Key={"slug": slug}).get("Item")

    def rename(self, slug, title):
        self.table.update_item(
            Key={"slug": slug},
            UpdateExpression="SET #title = :t",
            ConditionExpression="attribute_exists(#s)",
            ExpressionAttributeNames={"#title": "title", "#s": "slug"},
            ExpressionAttributeValues={":t": title},
        )

    def hide(self, slug, by):
        """Author withdraws a story: it stays in the table but leaves the feed."""
        self.table.update_item(
            Key={"slug": slug},
            UpdateExpression="SET #h = :h, #by = :by, #t = :t",
            ConditionExpression="attribute_exists(#s)",
            ExpressionAttributeNames={
                "#h": "hidden",
                "#by": "hidden_by",
                "#t": "hidden_at",
                "#s": "slug",
            },
            ExpressionAttributeValues={":h": True, ":by": by, ":t": int(self.clock())},
        )

    def feed(self, limit=FEED_LIMIT):
        """Public feed: newest first, hidden stories excluded, bodies left out."""
        resp = self.table.scan(
            ProjectionExpression="#s, #t, #h, #p",
            ExpressionAttributeNames={
                "#s": "slug",
                "#t": "title",
                "#h": "hidden",
                "#p": "published_at",
            },
        )
        items = [i for i in resp["Items"] if not i.get("hidden")]
        items.sort(key=lambda i: i["published_at"], reverse=True)
        return [
            {"slug": i["slug"], "title": i["title"], "published_at": i["published_at"]}
            for i in items[:limit]
        ]

    def archive(self, slug):
        """Editorial: take a published story out of circulation for good.
        Not wired to the API yet (planned for the admin console)."""
        self.table.update_item(
            Key={"slug": slug},
            UpdateExpression="SET #arch = :t",
            ConditionExpression="#st = :published",
            ExpressionAttributeNames={"#arch": "archived_at", "#st": "status"},
            ExpressionAttributeValues={":t": int(self.clock()), ":published": "published"},
        )
