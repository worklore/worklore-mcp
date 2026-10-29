"""Story library: the publish handler.

Each story is stored in one DynamoDB item together with the three most similar
stories already in the library (``similar``), so the reader page can show
"related" without a query at read time.
"""
import json
import logging
import re
import time
from decimal import Decimal

log = logging.getLogger("stories")

TABLE_NAME = "stories"
TOP_N = 3
SCORE_STEP = Decimal("0.0001")

_WORD = re.compile(r"[a-z0-9]+")


def words(text):
    return set(_WORD.findall((text or "").lower()))


def _jaccard(a, b):
    union = a | b
    return Decimal(len(a & b)) / Decimal(len(union)) if union else Decimal(0)


def similarity(a, b):
    """Shared-tag ratio (Jaccard), blended with shared words of the two bodies.

    Computed in Decimal, not float: the score is stored in DynamoDB, and boto3
    rejects Python floats ("Float types are not supported").
    """
    tag_score = _jaccard(set(a.get("tags", [])), set(b.get("tags", [])))
    word_score = _jaccard(words(a.get("body")), words(b.get("body")))
    score = Decimal("0.7") * tag_score + Decimal("0.3") * word_score
    return score.quantize(SCORE_STEP)


def to_dynamo(value):
    """Return ``value`` with every float converted to Decimal, recursively.

    Last line of defence before put_item: whatever computes a number later,
    a float must never reach boto3's serializer.
    """
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("non-finite number cannot be stored")
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_dynamo(v) for v in value]
    return value


def related(story, existing):
    scored = []
    for other in existing:
        if other["slug"] == story["slug"]:
            continue
        scored.append({"slug": other["slug"], "score": similarity(story, other)})
    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored[:TOP_N]


def validate(story):
    if not isinstance(story, dict):
        raise ValueError("body must be a JSON object")
    for k in ("slug", "title", "body"):
        if not story.get(k):
            raise ValueError(f"missing field: {k}")
    if not isinstance(story["slug"], str) or not re.fullmatch(r"[a-z0-9-]{3,80}", story["slug"]):
        raise ValueError("bad slug")
    tags = story.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise ValueError("tags must be a list of strings")


def publish(table, story):
    """Store ``story`` with its related stories. Returns the stored item."""
    validate(story)
    existing = table.scan(TableName=TABLE_NAME).get("Items", [])
    item = {
        "slug": story["slug"],
        "title": story["title"],
        "tags": sorted(set(story.get("tags", []))),
        "body": story["body"],
        "published_at": int(time.time()),
        "similar": related(story, existing),
    }
    item = to_dynamo(item)
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
