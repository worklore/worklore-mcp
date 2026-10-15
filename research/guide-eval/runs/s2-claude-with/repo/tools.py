"""Tool implementations. Each takes the store and the tool arguments, returns a dict."""
from decimal import Decimal


def _coerce(value):
    # DynamoDB hands back every number, at any depth, as Decimal; json can't encode
    # those. Integral values become int (schemas say "integer"), the rest float.
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: _coerce(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce(v) for v in value]
    return value


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
