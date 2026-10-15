"""Tool implementations. Each takes the store and the tool arguments, returns a dict."""
from decimal import Decimal


def _json_numbers(value):
    """Convert DynamoDB numbers throughout a value to JSON-compatible numbers."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {key: _json_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_numbers(item) for item in value]
    return value


def _coerce(note):
    note = _json_numbers(note)
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
