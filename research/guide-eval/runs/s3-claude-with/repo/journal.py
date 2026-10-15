"""daybook journal backend (in-memory store for this service).

A post carries two separate notions of time:

- ``date`` is content: the author's local calendar date ("YYYY-MM-DD"), like the
  date written at the top of a paper journal page. It is fixed at publish time
  and displayed exactly as stored, to every viewer, with no time zone conversion.
- ``received_at`` is metadata: the UTC instant the server received the post. It
  is used only to order feeds and is never shown as a date.
"""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_POSTS = []


def reset():
    _POSTS.clear()


def _utcnow():
    return datetime.now(timezone.utc)


def _author_local_date(entry, client_tz, now):
    """The author's calendar date for this post.

    Prefer the date captured on the author's device (``entry["date"]``); it is
    treated as an opaque calendar date. Otherwise derive it from the server
    instant in the author's reported zone -- never in UTC.
    """
    supplied = entry.get("date")
    if supplied is not None:
        try:
            return date.fromisoformat(supplied).isoformat()
        except (TypeError, ValueError):
            raise ValueError(f"invalid date {supplied!r}; expected YYYY-MM-DD")
    try:
        tz = ZoneInfo(client_tz)
    except (TypeError, ValueError, ZoneInfoNotFoundError):
        raise ValueError(f"unknown time zone {client_tz!r}")
    return now.astimezone(tz).date().isoformat()


def publish(entry, client_tz, now=None):
    """Store a new post.

    entry: {"author": str, "title": str, "body": str, "date": optional str}
        "date" is the author's local calendar date (YYYY-MM-DD) as captured on
        their device. If omitted, it is computed from the server clock in client_tz.
    client_tz: IANA zone reported by the author's browser, e.g. "Europe/Berlin".
    now: server clock override (aware datetime), used by tests.
    """
    now = now or _utcnow()
    post = dict(entry)
    post["client_tz"] = client_tz
    post["date"] = _author_local_date(entry, client_tz, now)
    post["received_at"] = now.astimezone(timezone.utc).isoformat()
    post["created_at"] = post["received_at"]  # kept for existing consumers
    _POSTS.append(post)
    return post


def display_date(post, viewer_tz=None):
    """Date shown on a post card: the author's date, exactly as written.

    viewer_tz is accepted for API compatibility but deliberately ignored --
    converting a calendar date between zones is what shifted days before.
    """
    return post["date"]


def feed():
    """Home feed, newest first by server receipt time (date as fallback)."""
    return sorted(
        _POSTS,
        key=lambda p: (p.get("received_at") or "", p["date"]),
        reverse=True,
    )
