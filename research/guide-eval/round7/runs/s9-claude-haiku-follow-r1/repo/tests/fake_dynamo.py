"""In-memory stand-in for a boto3 DynamoDB Table resource, for the tests.

Covers put_item, get_item, update_item and scan, with the expression rules
that matter for this service. It mirrors DynamoDB's documented behaviour
for reserved words (the real service keeps a list of ~570 of them; RESERVED
below is the subset that comes up in practice):

  * a bare reserved word in an UpdateExpression, ConditionExpression or
    FilterExpression raises ValidationException
    ("Attribute name is a reserved keyword"), exactly like the real service;
  * a bare reserved word in a ProjectionExpression does NOT raise on the real
    service: the attribute is simply absent from the returned item, and
    nothing in the response says so. This fake raises by default
    (strict_projection=True) so tests catch it; see FakeTable;
  * '#alias' placeholders resolved through ExpressionAttributeNames work in
    every expression, which is how DynamoDB tells you to spell any name.

Grammar supported: `SET a = :v [, ...]` and `REMOVE a [, ...]` in updates;
`=`, `<>`, `<`, `<=`, `>`, `>=`, attribute_exists(), attribute_not_exists(),
NOT, AND, OR and parentheses in conditions and filters.
"""
import copy
import re

RESERVED = frozenset("""
ADD AND ATTRIBUTE BINARY BY COMMENT COUNT DATA DATE DAY DELETE FALSE FROM GROUP HIDDEN HOUR
IN INDEX ITEM ITEMS KEY KEYS LEVEL LIST MAP MINUTE MONTH NAME NOT NULL NUMBER OF ON OR ORDER
PRIVATE PUBLIC QUERY REMOVE ROLE SCAN SECOND SELECT SET SIMILAR SIZE STATE STATUS STRING TABLE
TEXT TIMESTAMP TO TRUE TYPE UPDATE URL USER VALUE VALUES YEAR
""".split())

_KEYWORDS = {"SET", "REMOVE", "ADD", "DELETE", "AND", "OR", "NOT", "BETWEEN", "IN"}
_OPERATORS = {"=", "<>", "<", "<=", ">", ">=", "(", ")", ","}
_TOKEN = re.compile(r"\s*(#?[A-Za-z_][A-Za-z0-9_]*|:[A-Za-z_][A-Za-z0-9_]*|<>|<=|>=|[=<>(),])")


class ClientError(Exception):
    """Same shape as botocore.exceptions.ClientError (.response["Error"]["Code"])."""

    def __init__(self, code, message, operation):
        super().__init__(f"An error occurred ({code}) when calling the {operation} operation: {message}")
        self.response = {"Error": {"Code": code, "Message": message}}


def _tokens(expr):
    out, pos = [], 0
    while pos < len(expr):
        m = _TOKEN.match(expr, pos)
        if not m:
            if expr[pos:].strip():
                raise ValueError(f"fake_dynamo cannot parse expression near: {expr[pos:]!r}")
            break
        out.append(m.group(1)); pos = m.end()
    return out


class _Names:
    """Resolves attribute names in one API call and enforces the reserved-word rules."""

    def __init__(self, mapping, operation):
        self.mapping, self.operation, self.used = dict(mapping or {}), operation, set()

    def _invalid(self, kind, msg):
        raise ClientError("ValidationException", f"Invalid {kind}: {msg}", self.operation)

    def alias(self, kind, tok):
        if tok not in self.mapping:
            self._invalid(kind, f"An expression attribute name used in the document path is not defined; attribute name: {tok}")
        self.used.add(tok)
        return self.mapping[tok]

    def validate(self, kind, expr):
        """Raise like DynamoDB does for a bare reserved word or an unknown #alias."""
        toks = _tokens(expr)
        for i, t in enumerate(toks):
            if t.startswith("#"):
                self.alias(kind, t)
            elif t.startswith(":") or t in _OPERATORS or t.upper() in _KEYWORDS:
                continue
            elif i + 1 < len(toks) and toks[i + 1] == "(":
                continue  # function call: attribute_exists(...), size(...)
            elif t.upper() in RESERVED:
                self._invalid(kind, f"Attribute name is a reserved keyword; reserved keyword: {t}")
        return toks

    def resolve(self, tok):
        return self.mapping[tok] if tok.startswith("#") else tok

    def finish(self):
        unused = sorted(set(self.mapping) - self.used)
        if unused:
            raise ClientError("ValidationException", "Value provided in ExpressionAttributeNames unused in "
                              f"expressions: keys: {{{', '.join(unused)}}}", self.operation)


def _evaluate(toks, item, names, values):
    """Evaluate a validated condition/filter expression against one item."""
    pos = [0]
    peek = lambda: toks[pos[0]] if pos[0] < len(toks) else None  # noqa: E731

    def take():
        pos[0] += 1
        return toks[pos[0] - 1]

    def operand():
        t = take()
        return values[t] if t.startswith(":") else item.get(names.resolve(t))

    def primary():
        t = peek()
        if t == "(":
            take(); v = binary("OR"); take()
            return v
        if t.upper() == "NOT":
            take()
            return not primary()
        if t in ("attribute_exists", "attribute_not_exists"):
            take(); take(); present = names.resolve(take()) in item; take()
            return present if t == "attribute_exists" else not present
        left = operand(); op = take(); right = operand()
        if op in ("=", "<>"):
            return (left == right) if op == "=" else (left != right)
        if left is None or right is None:
            return False
        return {"<": left < right, "<=": left <= right, ">": left > right, ">=": left >= right}[op]

    def binary(word):
        sub = (lambda: binary("AND")) if word == "OR" else primary
        v = sub()
        while peek() and peek().upper() == word:
            take(); r = sub(); v = (v or r) if word == "OR" else (v and r)
        return v

    return binary("OR")


class FakeTable:
    def __init__(self, key="slug", strict_projection=True):
        # strict_projection=True raises on a bare reserved word in a ProjectionExpression,
        # where the real service drops it silently. Tests keep it on so that bug is loud;
        # pass False to reproduce the real service's behaviour.
        self.key, self._items, self.strict_projection = key, {}, strict_projection

    def _check(self, op, expr, current, names, values):
        if expr is not None and not _evaluate(names.validate("ConditionExpression", expr), current, names, values or {}):
            raise ClientError("ConditionalCheckFailedException", "The conditional request failed", op)

    def put_item(self, Item, ConditionExpression=None, ExpressionAttributeNames=None,
                 ExpressionAttributeValues=None, **_ignored):
        names = _Names(ExpressionAttributeNames, "PutItem")
        self._check("PutItem", ConditionExpression, self._items.get(Item[self.key], {}), names, ExpressionAttributeValues)
        names.finish()
        self._items[Item[self.key]] = copy.deepcopy(Item)
        return {}

    def get_item(self, Key, ProjectionExpression=None, ExpressionAttributeNames=None, **_ignored):
        names = _Names(ExpressionAttributeNames, "GetItem")
        item = self._items.get(Key[self.key])
        if item is None:
            return {}
        item = self._project(copy.deepcopy(item), ProjectionExpression, names)
        names.finish()
        return {"Item": item}

    def update_item(self, Key, UpdateExpression, ConditionExpression=None, ExpressionAttributeNames=None,
                    ExpressionAttributeValues=None, ReturnValues=None, **_ignored):
        names, values = _Names(ExpressionAttributeNames, "UpdateItem"), ExpressionAttributeValues or {}
        toks = names.validate("UpdateExpression", UpdateExpression)
        current = self._items.get(Key[self.key], {})
        self._check("UpdateItem", ConditionExpression, current, names, values)
        names.finish()
        item = copy.deepcopy(current) or dict(Key)
        clause, i = None, 0
        while i < len(toks):
            t = toks[i]
            if t.upper() in ("SET", "REMOVE"):
                clause = t.upper(); i += 1
            elif t == ",":
                i += 1
            elif clause == "SET" and i + 2 < len(toks) and toks[i + 1] == "=" and toks[i + 2].startswith(":"):
                item[names.resolve(t)] = values[toks[i + 2]]; i += 3
            elif clause == "REMOVE":
                item.pop(names.resolve(t), None); i += 1
            else:
                names._invalid("UpdateExpression", f"fake_dynamo does not support this syntax near {t!r}")
        self._items[Key[self.key]] = item
        return {"Attributes": copy.deepcopy(item)} if ReturnValues else {}

    def scan(self, ProjectionExpression=None, FilterExpression=None, ExpressionAttributeNames=None,
             ExpressionAttributeValues=None, **_ignored):
        names = _Names(ExpressionAttributeNames, "Scan")
        items = [copy.deepcopy(v) for v in self._items.values()]
        scanned = len(items)
        if FilterExpression:
            toks = names.validate("FilterExpression", FilterExpression)
            items = [i for i in items if _evaluate(toks, i, names, ExpressionAttributeValues or {})]
        items = [self._project(i, ProjectionExpression, names) for i in items]
        names.finish()
        return {"Items": items, "Count": len(items), "ScannedCount": scanned}

    def _project(self, item, expr, names):
        """Reserved words used bare are dropped from the result without any error
        (or raise, when strict_projection is set)."""
        if not expr:
            return item
        out = {}
        for path in [p.strip() for p in expr.split(",") if p.strip()]:
            if path.startswith("#"):
                attr = names.alias("ProjectionExpression", path)
            elif path.upper() in RESERVED:
                if self.strict_projection:
                    names._invalid("ProjectionExpression", f"Attribute name is a reserved keyword; reserved keyword: {path}")
                continue
            else:
                attr = path
            if attr in item:
                out[attr] = item[attr]
        return out
