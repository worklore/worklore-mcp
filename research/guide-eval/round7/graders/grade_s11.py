"""s11: The DynamoDB crash that only appears on your second write. Hidden answer key:
  publish() scores the new story against every existing one (similarity() returns a float: a Jaccard
  ratio, rounded) and stores the top-3 as similar=[{slug, score}]. boto3's TypeSerializer rejects
  floats ("Float types are not supported. Use Decimal types instead."), so put_item raises and the
  handler returns 500. The first publish survived because the table was empty: no existing stories,
  similar=[], no float anywhere in the item. Fix: store scores as int (percent) or Decimal at the
  boundary (or drop the feature). The method the story adds: a write-path test must seed one record
  before the write under test, otherwise the scoring path never runs.
PASS = ANSWER names float scores rejected by DynamoDB AND the hidden check (fixture's own fake table,
       not the repo's copy: publish one story, then a second) succeeds with no float in the stored item.
Extra: scoring_kept (second item still carries a non-empty `similar` list), seeded_test (a test in
       tests/ that writes a record and then publishes another), explains_empty_path, ran_tests.
"""
import ast, glob, importlib.util, json, os, re, sys
sys.dont_write_bytecode = True
from decimal import Decimal
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R); ans_l = ans.lower()
txt = run_text(R)

# ---- hidden fake table (the agent may have edited tests/fake_dynamo.py; this copy is the reference) ----
def _check(value):
    if isinstance(value, bool) or value is None or isinstance(value, (int, str, bytes, Decimal)): return
    if isinstance(value, float): raise TypeError("Float types are not supported. Use Decimal types instead.")
    if isinstance(value, dict):
        for v in value.values(): _check(v)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for v in value: _check(v)
        return
    raise TypeError(f"Unsupported type {type(value)!r}")

class HiddenTable:
    def __init__(self): self.items = {}
    def put_item(self, Item, **kw):
        _check(Item)
        if "slug" not in Item: raise ValueError("item is missing the key attribute 'slug'")
        self.items[Item["slug"]] = dict(Item); return {"ResponseMetadata": {"HTTPStatusCode": 200}}
    def get_item(self, Key, **kw):
        it = self.items.get(Key["slug"]); return {"Item": dict(it)} if it is not None else {}
    def scan(self, **kw): return {"Items": [dict(v) for v in self.items.values()], "Count": len(self.items)}
    def update_item(self, Key, **kw):
        for k in ("ExpressionAttributeValues",): _check(kw.get(k) or {})
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

S1 = {"slug": "why-my-cron-ran-twice", "title": "Why my cron ran twice", "tags": ["cron", "linux"],
      "body": "Two crontabs, one for root and one for me, both had the line."}
S2 = {"slug": "cron-mailto-silenced-my-errors", "title": "Cron MAILTO silenced my errors", "tags": ["cron", "email", "linux"],
      "body": "The line was there but MAILTO was empty, so cron threw the errors away."}

def floats_in(v):
    if isinstance(v, bool): return 0
    if isinstance(v, float): return 1
    if isinstance(v, dict): return sum(floats_in(x) for x in v.values())
    if isinstance(v, (list, tuple, set)): return sum(floats_in(x) for x in v)
    return 0

h = {"first_ok": False, "second_ok": False, "second_error": "", "stored_floats": None, "similar": None,
     "scoring_kept": False, "score_types": [], "import_error": ""}
try:
    src = os.path.join(repo, "src")
    sys.path.insert(0, src); sys.path.insert(0, os.path.join(repo, "tests"))
    spec = importlib.util.spec_from_file_location("app_under_test", os.path.join(src, "app.py"))
    app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)
    t = HiddenTable()
    pub = getattr(app, "publish", None)
    if pub is None:
        h["import_error"] = "no publish() in src/app.py"
    else:
        try:
            pub(t, dict(S1)); h["first_ok"] = S1["slug"] in t.items
        except Exception as e:
            h["second_error"] = f"first publish: {type(e).__name__}: {e}"
        if h["first_ok"]:
            try:
                pub(t, dict(S2))
                it = t.items.get(S2["slug"])
                h["second_ok"] = it is not None and floats_in(it) == 0
                if it is not None:
                    h["stored_floats"] = floats_in(it)
                    sim = it.get("similar")
                    h["similar"] = json.loads(json.dumps(sim, default=str)) if sim is not None else None
                    if isinstance(sim, list) and sim:
                        h["score_types"] = sorted({type(s.get("score")).__name__ for s in sim if isinstance(s, dict)})
                        h["scoring_kept"] = all(isinstance(s, dict) and "slug" in s and "score" in s
                                                and not isinstance(s["score"], float) and s["score"] is not None for s in sim)
            except Exception as e:
                h["second_error"] = f"{type(e).__name__}: {e}"
except Exception as e:
    h["import_error"] = f"{type(e).__name__}: {e}"

# ---- seeded test: a test in tests/ whose body (plus setUp) writes a record and then publishes another ----
WRITE = {"publish", "put_item", "handler", "seed", "store", "insert", "write", "create"}
def call_names(node):
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            out.append(name)
    return out
def writes(node): return sum(1 for n in call_names(node) if n in WRITE or n.startswith("seed") or n.startswith("publish"))
seeded_test, seeded_in = False, []
for path in sorted(glob.glob(os.path.join(repo, "tests", "**", "*.py"), recursive=True)):
    try: tree = ast.parse(read(path))
    except SyntaxError: continue
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        setup = sum(writes(f) for f in cls.body if isinstance(f, ast.FunctionDef) and f.name in ("setUp", "setUpClass"))
        for f in cls.body:
            if isinstance(f, ast.FunctionDef) and f.name.startswith("test") and writes(f) + setup >= 2:
                seeded_test = True; seeded_in.append(f"{os.path.relpath(path, repo)}::{f.name}")
    for f in [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test")]:
        if writes(f) >= 2: seeded_test = True; seeded_in.append(f"{os.path.relpath(path, repo)}::{f.name}")

# ---- answer ----
cause_named = ("float" in ans_l
               and bool(re.search(r"dynamo|decimal|typeserializer|not supported|boto", ans_l))
               and bool(re.search(r"score|similar|related|jaccard|ratio", ans_l)))
explains_empty_path = bool(re.search(r"empty (table|database|db|library)|table (was|is) empty|no (existing|other|prior|previous|stored) (stor(y|ies)|items?|records?|rows?|entries|data)"
                                     r"|nothing to (compare|score)|no (candidates|neighbou?rs|matches|scores|similar)|similar(ity)? (list|array)? ?(was|is) empty|first (write|publish|story|insert|item)", ans_l))
fix_named = bool(re.search(r"\bint\b|integer|percent|decimal|round\(|str\(|remov|drop", ans_l))
cmds = commands(R)
ran_tests = any(re.search(r"unittest|pytest|test_publish|tests/", c) for c in cmds) or bool(re.search(r"Ran \d+ tests? in", txt))
changed = git_changed(repo, base)

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"),
  "cause_named": cause_named, "explains_empty_path": explains_empty_path, "fix_named": fix_named,
  "hidden_first_ok": h["first_ok"], "hidden_second_ok": h["second_ok"], "hidden_second_error": h["second_error"],
  "hidden_import_error": h["import_error"], "stored_floats": h["stored_floats"], "similar_stored": h["similar"],
  "score_types": h["score_types"], "scoring_kept": h["scoring_kept"],
  "seeded_test": seeded_test, "seeded_test_in": seeded_in, "ran_tests": ran_tests,
  "app_changed": "src/app.py" in changed, "fake_changed": "tests/fake_dynamo.py" in changed, "tests_changed": [f for f in changed if f.startswith("tests/")],
  "changed_files": changed, "commands_issued": len(cmds), "answer_chars": len(ans),
}
g["PASS"] = bool(cause_named and h["first_ok"] and h["second_ok"])
print(json.dumps(g, indent=1, default=str))
