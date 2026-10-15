"""daybook journal backend (in-memory store for this service)."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_POSTS = []


def reset():
    _POSTS.clear()


def _utcnow():
    return datetime.now(timezone.utc)


def publish(entry, client_tz=None, now=None, date=None):
    """Store a new post.

    entry: {"author": str, "title": str, "body": str, "date": str (optional)}
    client_tz: optional IANA zone reported by the author's browser.
    now: server clock override (aware datetime), used by tests.
    date: author's local calendar date override if not in entry.
    """
    now = now or _utcnow()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    utc_now = now.astimezone(timezone.utc)

    post = dict(entry)
    if client_tz is not None:
        post["client_tz"] = client_tz

    received_at_str = utc_now.isoformat()
    post["received_at"] = received_at_str
    post["created_at"] = received_at_str

    # Date is content (author's local calendar date), treated as an opaque string.
    if date is not None:
        post["date"] = str(date)
    elif "date" in post and post["date"] is not None:
        post["date"] = str(post["date"])
    else:
        post["date"] = utc_now.date().isoformat()

    _POSTS.append(post)
    return post


def display_date(post, viewer_tz=None):
    """Date shown on a post card, displayed exactly as written."""
    return post["date"]


def _sort_key(p):
    r = p.get("received_at")
    if r is not None:
        if isinstance(r, datetime):
            if r.tzinfo is None:
                r = r.replace(tzinfo=timezone.utc)
            r = r.astimezone(timezone.utc).isoformat()
        return (str(r), str(p.get("date", "")), str(p.get("author", "")))
    return (str(p.get("date", "")), str(p.get("date", "")), str(p.get("author", "")))


def feed():
    """Home feed, newest first."""
    return sorted(_POSTS, key=_sort_key, reverse=True)
