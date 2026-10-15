"""Storage layer.

DynamoStore stands in for the real DynamoDB table (boto3 resource API). Like the
real boto3 TypeDeserializer, every number it hands back -- at any depth -- is a
decimal.Decimal. FakeStore is the in-memory store the unit tests use.
"""
import copy
import os
from decimal import Decimal

SEED = {
    "n1": {
        "id": "n1",
        "title": "Ship the importer",
        "word_count": 412,
        "stats": {"views": 37, "rating": 4.5, "revisions": [1, 2, 3]},
        "tags": ["work", "q4"],
    },
    "n2": {
        "id": "n2",
        "title": "Groceries",
        "word_count": 18,
        "stats": {"views": 3, "rating": 3.0, "revisions": [1]},
        "tags": ["home"],
    },
}


def _to_dynamo(value):
    """What boto3's TypeDeserializer does to numbers: Decimal, everywhere."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamo(v) for v in value]
    return value


class DynamoStore:
    """Production store (simulated DynamoDB table)."""

    def __init__(self, items=None):
        self._items = copy.deepcopy(items if items is not None else SEED)

    def get(self, note_id):
        item = self._items.get(note_id)
        return _to_dynamo(copy.deepcopy(item)) if item is not None else None

    def scan(self):
        return [_to_dynamo(copy.deepcopy(i)) for i in self._items.values()]


class FakeStore:
    """In-memory store for tests, with DynamoDB's read-time number types."""

    def __init__(self, items=None):
        self._items = copy.deepcopy(items if items is not None else SEED)

    def get(self, note_id):
        item = self._items.get(note_id)
        return _to_dynamo(copy.deepcopy(item)) if item is not None else None

    def scan(self):
        return [_to_dynamo(copy.deepcopy(i)) for i in self._items.values()]


def get_store():
    if os.environ.get("PRODUCTION_DB") == "1":
        return DynamoStore()
    return FakeStore()
