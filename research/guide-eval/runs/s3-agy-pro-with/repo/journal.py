"""daybook journal backend (in-memory store for this service)."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_POSTS = []


def reset():
    _POSTS.clear()


def _utcnow():
    return datetime.now(timezone.utc)


def publish(entry, local_date, now=None):
    """Store a new post.

    entry: {"author": str, "title": str, "body": str}
    local_date: The author's local calendar date as a string (e.g. "2026-03-10").
    now: server clock override (aware datetime), used by tests.
    """
    now = now or _utcnow()
    post = dict(entry)
    post["date"] = local_date
    post["received_at"] = now.astimezone(timezone.utc).isoformat()
    _POSTS.append(post)
    return post


def display_date(post, viewer_tz):
    """Date shown on a post card, exactly as written."""
    return post["date"]


def feed():
    """Home feed, newest first."""
    return sorted(_POSTS, key=lambda p: (p["received_at"], p["date"]), reverse=True)
