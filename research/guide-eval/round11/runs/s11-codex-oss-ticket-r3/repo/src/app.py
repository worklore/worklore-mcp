"""Story library: the publish handler.

Each story is stored in one DynamoDB item together with the three most similar
stories already in the library (``similar``), so the reader page can show
"related" without a query at read time.
"""

import json
import logging
import re
import time

log = logging.getLogger("stories")

TABLE_NAME = "stories"
TOP_N = 3

_WORD = re.compile(r"[a-z0-9]+")


def words(text):
    """Return a set of lowercase alphanumeric words from *text*."""
    return set(_WORD.findall((text or "").lower()))


def similarity(a, b):
    """Shared-tag ratio (Jaccard), blended with shared words of the two bodies."""
    ta, tb = set(a.get("tags", [])), set(b.get("tags", []))
    tag_score = len(ta & tb) / len(ta | tb) if (ta | tb) else 0
    wa, wb = words(a.get("body")), words(b.get("body"))
    word_score = len(wa & wb) / len(wa | wb) if (wa | wb) else 0
    return round(0.7 * tag_score + 0.3 * word_score, 4)


def related(story, existing):
    """Return the top ``TOP_N`` related stories.

    The original implementation stored raw ``float`` similarity scores in the
    DynamoDB ``similar`` attribute, which DynamoDB rejects (it requires ``Decimal``
    or integer types). The first publish succeeded because the table was empty,
    resulting in an empty ``similar`` list, so no floats were written. Subsequent
    publishes attempted to write a ``float`` ``score`` and raised:

    ``TypeError: Float types are not supported. Use Decimal types instead.``

    The fix converts the similarity (0‑1) to an integer percentage before storing.
    """
    scored = []
    for other in existing:
        if other["slug"] == story["slug"]:
            continue
        raw_score = similarity(story, other)
        int_score = int(round(raw_score * 100))
        scored.append({"slug": other["slug"], "score": int_score})
    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored[:TOP_N]


def validate(story):
    """Validate required fields and slug format."""
    for k in ("slug", "title", "body"):
        if not story.get(k):
            raise ValueError(f"missing field: {k}")
    if not re.fullmatch(r"[a-z0-9-]{3,80}", story["slug"]):
        raise ValueError("bad slug")


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
    table.put_item(Item=item)
    log.info("publish slug=%s similar=%d stored", item["slug"], len(item["similar"]))
    return item


def handler(event, table):
    """Lambda‑style entry point for POST /stories. Body is the story as JSON."""
    try:
        story = json.loads(event.get("body") or "{}")
        stored = publish(table, story)
        return {"statusCode": 201, "body": json.dumps({"slug": stored["slug"]})}
    except ValueError as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    except Exception:
        log.exception("publish failed")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error"})}

