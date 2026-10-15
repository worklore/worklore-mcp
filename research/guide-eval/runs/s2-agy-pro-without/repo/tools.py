"""Tool implementations. Each takes the store and the tool arguments, returns a dict."""

def _coerce(obj):
    # DynamoDB hands numbers back as Decimal; make them JSON-friendly.
    # Recurse through dicts and lists.
    from decimal import Decimal
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _coerce(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_coerce(v) for v in obj]
    return obj

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
