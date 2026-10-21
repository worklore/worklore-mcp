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
            ConditionExpression="attribute_not_exists(slug)",
        )

    def get(self, slug):
        return self.table.get_item(Key={"slug": slug}).get("Item")

    def rename(self, slug, title):
        self.table.update_item(
            Key={"slug": slug},
            UpdateExpression="SET title = :t",
            ConditionExpression="attribute_exists(slug)",
            ExpressionAttributeValues={":t": title},
        )

    def hide(self, slug, by):
        """Author withdraws a story: it stays in the table but leaves the feed."""
        self.table.update_item(
            Key={"slug": slug},
            UpdateExpression="SET #h = :h, #hb = :by, #ha = :t",
            ConditionExpression="attribute_exists(slug)",
            ExpressionAttributeValues={":h": True, ":by": by, ":t": int(self.clock())},
            ExpressionAttributeNames={"#h": "hidden", "#hb": "hidden_by", "#ha": "hidden_at"},
        )

    def feed(self, limit=FEED_LIMIT):
        """Public feed: newest first, hidden stories excluded, bodies left out."""
        resp = self.table.scan(ProjectionExpression="slug, title, hidden, published_at")
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
            UpdateExpression="SET archived_at = :t",
            ConditionExpression="status = :published",
            ExpressionAttributeValues={":t": int(self.clock()), ":published": "published"},
        )
