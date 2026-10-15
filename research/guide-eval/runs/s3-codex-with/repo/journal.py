"""daybook journal backend (in-memory store for this service)."""
from datetime import datetime, timezone

_POSTS = []


def reset():
    _POSTS.clear()


def _utcnow():
    return datetime.now(timezone.utc)


def publish(entry, client_tz, now=None):
    """Store a new post.

    entry: {"author": str, "title": str, "body": str, "date": "YYYY-MM-DD"}.
           date is the author's calendar date, captured on their device.
    client_tz: IANA zone reported by the author's browser, e.g. "Europe/Berlin".
    now: server clock override (aware datetime), used by tests.
    """
    if "date" not in entry:
        raise ValueError("entry must include the author's local date")
    now = now if now is not None else _utcnow()
    post = dict(entry)
    post["client_tz"] = client_tz
    post["received_at"] = now.astimezone(timezone.utc).isoformat()
    post["created_at"] = post["received_at"]
    _POSTS.append(post)
    return post


def display_date(post, viewer_tz):
    """Show the author's calendar date unchanged, regardless of viewer zone."""
    return post["date"]


def feed():
    """Home feed, newest first."""
    return sorted(_POSTS, key=lambda p: p.get("received_at") or p["date"], reverse=True)
