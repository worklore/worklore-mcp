#!/usr/bin/env python3
"""Third round on the same random 1,000 (random-1000/): output contracts, mcp-drill's method.

Read-only and anonymous, like rounds 1-2: initialize + tools/list (all pages), never tools/call.
For every tool: does it declare an outputSchema, and would that schema reject a corrupted but
well-typed response? The corruption and validation below are copied verbatim from
mcp-drill (MIT, Timur Rakhmatullin, https://github.com/TimurRakhmatullin86/mcp-drill,
src/mcp_drill/scorecard.py at commit ccaee07267a8), so the tiers mean exactly what his do:
no schema / vacuous (corrupted payload still validates) / enforceable (schema rejects it).

Writes random-1000/contracts.jsonl (one row per server, with the tools' names and output schemas)
and prints the aggregate. Run with the venv that has jsonschema: .venv/bin/python contracts.py
"""
import concurrent.futures as cf, json, os, sys
from collections import Counter
from typing import Any

import jsonschema

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan import rpc, INIT

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "random-1000")

# ---- verbatim from mcp-drill scorecard.py (ccaee07) -------------------------------------------
_CORRUPT_STRING = "mcp-drill-corruption"
_CORRUPT_INT = -999999999
_CORRUPT_NUMBER = -1.5e308


def _is_fastmcp_wrapped(schema: dict[str, Any]) -> bool:
    return schema.get("x-fastmcp-wrap-result") is True


def accepts_corruption(schema: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(schema, dict) or not schema:
        return True, "no schema"
    instance = _corruption_instance(schema)
    try:
        jsonschema.validate(instance, schema)
        return True, "corrupted payload validates against the declared schema"
    except jsonschema.ValidationError:
        return False, "declared schema rejects the corrupted payload"
    except Exception:  # noqa: BLE001 - a schema we cannot even compile enforces nothing
        return True, "schema is not a compilable JSON Schema"


def _corruption_instance(node: Any) -> Any:
    if not isinstance(node, dict):
        return _CORRUPT_STRING
    for comb in ("allOf", "anyOf", "oneOf"):
        options = node.get(comb)
        if isinstance(options, list) and options:
            return _corruption_instance(options[0])
    t = node.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), t[0] if t else None)
    if t == "object" or "properties" in node:
        props = node.get("properties") or {}
        required = node.get("required") or list(props.keys())
        return {key: _corruption_instance(props.get(key, {})) for key in required}
    if t == "array":
        items = node.get("items")
        return [_corruption_instance(items)] if isinstance(items, dict) else []
    if t == "integer":
        return _CORRUPT_INT
    if t == "number":
        return _CORRUPT_NUMBER
    if t == "boolean":
        return False
    if t == "null":
        return None
    return _CORRUPT_STRING
# -----------------------------------------------------------------------------------------------


def tier(tool):
    s = tool.get("outputSchema")
    if not isinstance(s, dict):
        return "none", None
    acc, why = accepts_corruption(s)
    return ("vacuous" if acc else "enforceable"), why


def check(s):
    url, row = s["url"], {"server": s}
    init = rpc(url, "initialize", INIT)
    res = (init.get("msg") or {}).get("result") if isinstance(init.get("msg"), dict) else None
    if not res:
        row["error"] = init.get("error") or f"initialize HTTP {init.get('status')}"
        return row
    sid = init.get("sid")
    rpc(url, "notifications/initialized", None, sid, notify=True)
    row["server_version"] = (res.get("serverInfo") or {}).get("version")
    row["protocol"] = res.get("protocolVersion")
    tools, cursor, pages = [], None, 0
    while pages < 20:
        tl = rpc(url, "tools/list", {"cursor": cursor} if cursor else {}, sid)
        r = (tl.get("msg") or {}).get("result") if isinstance(tl.get("msg"), dict) else None
        if r is None:
            row["error"] = tl.get("error") or f"tools/list HTTP {tl.get('status')}"
            break
        tools += [t for t in (r.get("tools") or []) if isinstance(t, dict)]
        pages += 1
        cursor = r.get("nextCursor")
        if not cursor:
            break
    row["tools"] = []
    for t in tools:
        k, why = tier(t)
        row["tools"].append({"name": t.get("name"), "tier": k, "why": why,
                             "fastmcp_wrapped": isinstance(t.get("outputSchema"), dict) and _is_fastmcp_wrapped(t["outputSchema"]),
                             "outputSchema": t.get("outputSchema")})
    return row


def main():
    open_ = []
    for line in open(os.path.join(D, "results.jsonl")):
        r = json.loads(line)
        if r["facts"].get("tools_status") == 200 and r["facts"].get("tool_count"):
            open_.append(r["server"])
    out = os.path.join(D, "contracts.jsonl")
    with cf.ThreadPoolExecutor(16) as ex, open(out, "w") as f:
        for row in ex.map(check, open_):
            f.write(json.dumps(row) + "\n")
    summarize(out, len(open_))


def summarize(path, asked=None):
    rows = [json.loads(l) for l in open(path)]
    ok = [r for r in rows if r.get("tools")]
    tools = [t for r in ok for t in r["tools"]]
    c = Counter(t["tier"] for t in tools)
    n = len(tools)
    srv = Counter("enforceable" if any(t["tier"] == "enforceable" for t in r["tools"]) else
                  "vacuous" if any(t["tier"] == "vacuous" for t in r["tools"]) else "none" for r in ok)
    print(f"servers asked {asked or len(rows)} · answered with tools {len(ok)} · tools {n}")
    for k in ("none", "vacuous", "enforceable"):
        print(f"  {k:12s} {c[k]:5d}  {100 * c[k] / n:5.1f}%   servers whose best tool is {k}: {srv[k]}")
    print("  fastmcp-wrapped:", sum(t["fastmcp_wrapped"] for t in tools),
          "· uncompilable schemas:", sum(1 for t in tools if t["why"] == "schema is not a compilable JSON Schema"))


if __name__ == "__main__":
    summarize(sys.argv[2]) if sys.argv[1:2] == ["--summary"] else main()
