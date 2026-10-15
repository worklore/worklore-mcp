"""Tool implementations. Each takes the store and the tool arguments, returns a dict."""


from decimal import Decimal


def _plain(v):
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_plain(x) for x in v]
    return v


def _coerce(note):
    note = _plain(note)
    # DynamoDB hands numbers back as Decimal; make the obvious ones JSON-friendly.
    note = dict(note)
    if "word_count" in note:
        note["word_count"] = int(note["word_count"])
    return note


def get_note(store, note_id):
    note = store.get(note_id)
    if note is None:
        raise KeyError(f"no note {note_id!r}")
    return _coerce(note)


def list_notes(store, tag=None):
    notes = [_coerce(n) for n in store.scan()]
    if tag:
        notes = [n for n in notes if tag in n.get("tags", [])]
    return {
        "notes": [
            {"id": n["id"], "title": n["title"], "word_count": n["word_count"]}
            for n in sorted(notes, key=lambda n: n["id"])
        ],
        "count": len(notes),
    }
