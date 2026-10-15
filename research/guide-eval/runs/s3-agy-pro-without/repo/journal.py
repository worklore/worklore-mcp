"""daybook journal backend (in-memory store for this service)."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_POSTS = []


def reset():
    _POSTS.clear()


def _utcnow():
    return datetime.now(timezone.utc)


def publish(entry, client_tz, now=None):
    """Store a new post.

    entry: {"author": str, "title": str, "body": str}
    client_tz: IANA zone reported by the author's browser, e.g. "Europe/Berlin".
    now: server clock override (aware datetime), used by tests.
    """
    now = now or _utcnow()
    post = dict(entry)
    post["client_tz"] = client_tz
    post["created_at"] = now.astimezone(timezone.utc).isoformat()
    # Dates are always generated on the server, in UTC, so they are consistent.
    post["date"] = now.astimezone(timezone.utc).date().isoformat()
    _POSTS.append(post)
    return post


def display_date(post, viewer_tz):
    """Date shown on a post card, converted to the viewer's zone."""
    dt = datetime.fromisoformat(post["created_at"])
    return dt.astimezone(ZoneInfo(viewer_tz)).date().isoformat()


def feed():
    """Home feed, newest first."""
    return sorted(_POSTS, key=lambda p: (p["created_at"], p["author"]), reverse=True)
