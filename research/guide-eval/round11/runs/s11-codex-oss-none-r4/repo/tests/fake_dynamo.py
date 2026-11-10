"""In-memory stand-in for a boto3 DynamoDB Table resource.

It stores items in a dict and validates values the way boto3's TypeSerializer
does, so a test fails on the same inputs a real table would reject.
"""
from decimal import Decimal


def _check(value, path="Item"):
    if isinstance(value, bool) or value is None or isinstance(value, (int, str, bytes, Decimal)):
        return
    if isinstance(value, float):
        raise TypeError("Float types are not supported. Use Decimal types instead.")
    if isinstance(value, dict):
        for k, v in value.items():
            _check(v, f"{path}.{k}")
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for i, v in enumerate(value):
            _check(v, f"{path}[{i}]")
        return
    raise TypeError(f"Unsupported type {type(value)!r} for value at {path}")


class FakeTable:
    def __init__(self, key="slug"):
        self.key = key
        self.items = {}

    def put_item(self, Item, **kwargs):
        _check(Item)
        if self.key not in Item:
            raise ValueError(f"item is missing the key attribute {self.key!r}")
        self.items[Item[self.key]] = dict(Item)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def get_item(self, Key, **kwargs):
        item = self.items.get(Key[self.key])
        return {"Item": dict(item)} if item is not None else {}

    def scan(self, **kwargs):
        return {"Items": [dict(v) for v in self.items.values()], "Count": len(self.items)}
