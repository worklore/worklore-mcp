"""Story library: the publish handler.

Each story is stored in one DynamoDB item together with the three most similar
stories already in the library (``similar``), so the reader page can show
"related" without a query at read time.
"""
import json
import logging
import re
import math
import time
from decimal import Decimal

log = logging.getLogger("stories")

TABLE_NAME = "stories"
TOP_N = 3

_WORD = re.compile(r"[a-z0-9]+")


def words(text):
    return set(_WORD.findall((text or "").lower()))


def similarity(a, b):
    """Shared-tag ratio (Jaccard), blended with shared words of the two bodies."""
    ta, tb = set(a.get("tags", [])), set(b.get("tags", []))
    tag_score = len(ta & tb) / len(ta | tb) if (ta | tb) else 0
    wa, wb = words(a.get("body")), words(b.get("body"))
    word_score = len(wa & wb) / len(wa | wb) if (wa | wb) else 0
    return round(0.7 * tag_score + 0.3 * word_score, 4)


def related(story, existing):
    scored = []
    for other in existing:
        if other["slug"] == story["slug"]:
            continue
        scored.append({"slug": other["slug"], "score": similarity(story, other)})
    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored[:TOP_N]


def to_dynamo(value):
    """Return ``value`` with every float replaced by a Decimal.

    boto3's DynamoDB serializer rejects floats outright, so every item goes
    through this before ``put_item``.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"cannot store non-finite number: {value!r}")
        return Decimal(repr(value))
    if isinstance(value, dict):
        return {k: to_dynamo(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_dynamo(v) for v in value]
    return value


def validate(story):
    for k in ("slug", "title", "body"):
        if not story.get(k):
            raise ValueError(f"missing field: {k}")
    if not re.fullmatch(r"[a-z0-9-]{3,80}", story["slug"]):
        raise ValueError("bad slug")
    tags = story.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise ValueError("tags must be a list of strings")


def publish(table, story):
    """Store ``story`` with its related stories. Returns the stored item."""
    validate(story)
    existing = table.scan(TableName=TABLE_NAME).get("Items", [])
    item = to_dynamo({
        "slug": story["slug"],
        "title": story["title"],
        "tags": sorted(set(story.get("tags", []))),
        "body": story["body"],
        "published_at": int(time.time()),
        "similar": related(story, existing),
    })
    table.put_item(Item=item)
    log.info("publish slug=%s similar=%d stored", item["slug"], len(item["similar"]))
    return item


def handler(event, table):
    """Lambda-style entry point for POST /stories. Body is the story as JSON."""
    try:
        story = json.loads(event.get("body") or "{}")
        stored = publish(table, story)
        return {"statusCode": 201, "body": json.dumps({"slug": stored["slug"]})}
    except ValueError as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    except Exception:
        log.exception("publish failed")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error"})}
