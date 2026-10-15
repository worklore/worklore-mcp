"""daybook journal backend (in-memory store for this service)."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_POSTS = []


def reset():
    _POSTS.clear()


def _utcnow():
    return datetime.now(timezone.utc)


def _zone(name):
    """Resolve an IANA zone name, falling back to UTC for missing/bogus values."""
    try:
        return ZoneInfo(name) if name else timezone.utc
    except (ZoneInfoNotFoundError, ValueError):
        return timezone.utc


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
    # A journal entry's date is the calendar day where the author wrote it,
    # not the UTC day (which is off by one for much of the world).
    post["date"] = now.astimezone(_zone(client_tz)).date().isoformat()
    _POSTS.append(post)
    return post


def display_date(post, viewer_tz):
    """Date shown on a post card.

    The date is a calendar day in the author's zone, not an instant, so it is
    shown as-is to every viewer; converting it through any time of day would
    shift it by one for zones far enough from that anchor.
    """
    return post["date"]


def feed():
    """Home feed, newest first (by actual publish time, not local date)."""
    return sorted(_POSTS, key=lambda p: p["created_at"], reverse=True)
