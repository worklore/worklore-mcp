"""Tool implementations. Each takes the store and the tool arguments, returns a dict."""
from decimal import Decimal


def _coerce(val):
    # DynamoDB hands numbers back as Decimal; make the obvious ones JSON-friendly.
    if isinstance(val, Decimal):
        return int(val) if val % 1 == 0 else float(val)
    if isinstance(val, dict):
        note = dict(val)
        if "word_count" in note and note["word_count"] is not None:
            note["word_count"] = int(note["word_count"])
        if "stats" in note and isinstance(note["stats"], dict):
            stats = dict(note["stats"])
            if "views" in stats and stats["views"] is not None:
                stats["views"] = int(stats["views"])
            if "rating" in stats and stats["rating"] is not None:
                stats["rating"] = float(stats["rating"])
            if "revisions" in stats and isinstance(stats["revisions"], (list, tuple)):
                stats["revisions"] = [int(r) for r in stats["revisions"]]
            note["stats"] = stats
        return {k: _coerce(v) for k, v in note.items()}
    if isinstance(val, list):
        return [_coerce(v) for v in val]
    return val


def get_note(store, note_id):
    note = store.get(note_id)
    if note is None:
        raise KeyError(f"no note {note_id!r}")
    return _coerce(note)


def list_notes(store, tag=None):
    notes = [_coerce(n) for n in store.scan()]
    if tag:
        notes = [n for n in notes if tag in (n.get("tags") or [])]
    return {
        "notes": [
            {"id": n["id"], "title": n["title"], "word_count": n["word_count"]}
            for n in sorted(notes, key=lambda n: n.get("id", ""))
        ],
        "count": len(notes),
    }

