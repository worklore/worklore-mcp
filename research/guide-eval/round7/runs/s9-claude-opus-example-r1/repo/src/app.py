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


def _names(*attrs):
    """ExpressionAttributeNames for `attrs`, aliased as '#<attr>'.

    House rule: every attribute name in every DynamoDB expression goes through
    an alias -- never bare. DynamoDB reserves ~570 ordinary words (hidden,
    status, name, date, ...). A bare one fails loudly in Update/Condition/
    Filter/KeyCondition expressions, but in a ProjectionExpression it is
    silently dropped from the returned item. tests/test_feed.py enforces this.
    """
    return {f"#{a}": a for a in attrs}


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
            ConditionExpression="attribute_not_exists(#slug)",
            ExpressionAttributeNames=_names("slug"),
        )

    def get(self, slug):
        return self.table.get_item(Key={"slug": slug}).get("Item")

    def rename(self, slug, title):
        self.table.update_item(
            Key={"slug": slug},
            UpdateExpression="SET #title = :t",
            ConditionExpression="attribute_exists(#slug)",
            ExpressionAttributeNames=_names("title", "slug"),
            ExpressionAttributeValues={":t": title},
        )

    def hide(self, slug, by):
        """Author withdraws a story: it stays in the table but leaves the feed."""
        self.table.update_item(
            Key={"slug": slug},
            UpdateExpression="SET #hidden = :h, #hidden_by = :by, #hidden_at = :t",
            ConditionExpression="attribute_exists(#slug)",
            ExpressionAttributeNames=_names("hidden", "hidden_by", "hidden_at", "slug"),
            ExpressionAttributeValues={":h": True, ":by": by, ":t": int(self.clock())},
        )

    def feed(self, limit=FEED_LIMIT):
        """Public feed: newest first, hidden stories excluded, bodies left out."""
        fields = ("slug", "title", "hidden", "published_at")
        kwargs = {
            "ProjectionExpression": ", ".join(f"#{f}" for f in fields),
            "ExpressionAttributeNames": _names(*fields),
        }
        items = []
        while True:  # a scan page stops at 1 MB; follow LastEvaluatedKey
            resp = self.table.scan(**kwargs)
            items.extend(i for i in resp["Items"] if not i.get("hidden"))
            if "LastEvaluatedKey" not in resp:
                break
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
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
            UpdateExpression="SET #archived_at = :t",
            ConditionExpression="#status = :published",
            ExpressionAttributeNames=_names("archived_at", "status"),
            ExpressionAttributeValues={":t": int(self.clock()), ":published": "published"},
        )
