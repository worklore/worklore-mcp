"""s9: DynamoDB reserved words. Hidden answer key:
  Bug 1 (loud):   src/app.py hide() -> UpdateExpression="SET hidden = :h, ..." with `hidden` bare;
                  DynamoDB rejects it: ValidationException "Attribute name is a reserved keyword: hidden".
                  Fix: alias (#h) via ExpressionAttributeNames, or rename the attribute consistently.
  Bug 2 (silent): src/app.py feed() -> ProjectionExpression="slug, title, hidden, published_at" with
                  `hidden` bare; the field comes back absent (no error), so `not item.get("hidden")`
                  keeps every hidden story in the feed. Fix: alias in the projection, drop the
                  projection, or move the filter to an aliased FilterExpression.
  Latent (bonus): archive() -> ConditionExpression="status = :published", `status` is reserved too.
PASS = bug1 named + bug2 named + hidden check (pristine fake from the base commit): hide() succeeds,
       a hidden story is absent from feed(), an unhidden one is still present.
Bonus flags: blanket (no bare reserved word left in any expression literal in src/, incl. status),
             seeded_test (a test hides a story and asserts it is gone from the feed),
             latent_named (ANSWER mentions status/archive).
"""
import json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R); ans_l = ans.lower()

RESERVED = set("""ADD AND ATTRIBUTE BINARY BY COMMENT COUNT DATA DATE DAY DELETE FALSE FROM GROUP HIDDEN HOUR
IN INDEX ITEM ITEMS KEY KEYS LEVEL LIST MAP MINUTE MONTH NAME NOT NULL NUMBER OF ON OR ORDER PRIVATE PUBLIC
QUERY REMOVE ROLE SCAN SECOND SELECT SET SIMILAR SIZE STATE STATUS STRING TABLE TEXT TIMESTAMP TO TRUE TYPE
UPDATE URL USER VALUE VALUES YEAR""".split())
KEYWORDS = {"SET", "REMOVE", "ADD", "DELETE", "AND", "OR", "NOT", "BETWEEN", "IN"}
KINDS = ("UpdateExpression", "ConditionExpression", "ProjectionExpression", "FilterExpression", "KeyConditionExpression")
LIT = r"(?:[fFrRbB]{0,2}(?:\"[^\"\n]*\"|'[^'\n]*')\s*)+"

def src_files():
    out = {}
    for root, _, files in os.walk(os.path.join(repo, "src")):
        for f in files:
            if f.endswith(".py"):
                out[os.path.relpath(os.path.join(root, f), repo)] = read(os.path.join(root, f))
    return out

def bare_reserved(text):
    """[(kind, word)] for every string-literal expression in `text` that uses a reserved word bare."""
    hits = []
    for kind in KINDS:
        for m in re.finditer(kind + r"\s*=\s*(" + LIT + ")", text):
            expr = " ".join(re.findall(r"[\"']([^\"'\n]*)[\"']", m.group(1)))
            toks = re.findall(r"#?[A-Za-z_][A-Za-z0-9_]*|:[A-Za-z_][A-Za-z0-9_]*|\(", expr)
            for i, t in enumerate(toks):
                if t[0] in "#:(" or t.upper() in KEYWORDS or (i + 1 < len(toks) and toks[i + 1] == "("):
                    continue
                if t.upper() in RESERVED:
                    hits.append((kind, t))
    return hits

src = src_files()
bare = sorted({f"{k}:{w}" for t in src.values() for k, w in bare_reserved(t)})
update_bare = [b for b in bare if b.startswith(("UpdateExpression", "ConditionExpression")) and b.endswith(":hidden")]
projection_bare = [b for b in bare if b.startswith("ProjectionExpression")]

# ---- hidden behavioural check, against the fixture's ORIGINAL fake (the agent may have edited tests/) ----
HIDDEN = r'''
import importlib, importlib.util, json, sys, traceback
fake_path, repo = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("_pristine_fake", fake_path)
fake = importlib.util.module_from_spec(spec); spec.loader.exec_module(fake)
sys.path.insert(0, repo)
out = {"hide_ok": False, "feed_ok": False, "visible_ok": False, "error": None}
def slug_of(s):
    if isinstance(s, str): return s
    if isinstance(s, dict): return s.get("slug")
    return getattr(s, "slug", None)
try:
    app = importlib.import_module("src.app")
    lib = app.StoryLibrary(fake.FakeTable())
    lib.publish("alpha", "Alpha", "body a", "ann")
    lib.publish("beta", "Beta", "body b", "bob")
    try:
        lib.hide("alpha", "ann"); out["hide_ok"] = True
    except Exception as e:
        out["error"] = "hide: " + repr(e)[:300]
    slugs = [slug_of(s) for s in lib.feed()]
    out["feed"] = slugs
    out["feed_ok"] = out["hide_ok"] and "alpha" not in slugs
    out["visible_ok"] = "beta" in slugs
except Exception as e:
    out["error"] = (out["error"] or "") + " | " + repr(e)[:300] + " " + traceback.format_exc()[-400:]
print(json.dumps(out))
'''
hidden = {"hide_ok": False, "feed_ok": False, "visible_ok": False, "error": "not run"}
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")  # the grader must not leave __pycache__ in the agent's repo
with tempfile.TemporaryDirectory() as td:
    pristine = subprocess.run(["git", "show", f"{base}:tests/fake_dynamo.py"], cwd=repo, capture_output=True, text=True).stdout
    if not pristine.strip():
        pristine = read(os.path.join(repo, "tests", "fake_dynamo.py"))
    fp = os.path.join(td, "fake_dynamo.py"); open(fp, "w").write(pristine)
    hp = os.path.join(td, "hidden_check.py"); open(hp, "w").write(HIDDEN)
    try:
        p = subprocess.run([sys.executable, "-I", hp, fp, repo], cwd=td, capture_output=True, text=True, timeout=120, env=ENV)
        line = [l for l in p.stdout.splitlines() if l.startswith("{")]
        hidden = json.loads(line[-1]) if line else {"hide_ok": False, "feed_ok": False, "visible_ok": False, "error": (p.stderr or p.stdout)[-400:]}
    except Exception as e:
        hidden["error"] = repr(e)[:300]

# ---- the fixture's own tests, as the README says to run them ----
try:
    t = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], cwd=repo, capture_output=True, text=True, timeout=180, env=ENV)
    tests_pass = t.returncode == 0
    tests_tail = (t.stderr or t.stdout).strip().splitlines()[-1:]
except Exception as e:
    tests_pass, tests_tail = False, [repr(e)[:200]]

# ---- seeded test: a test function that hides and asserts absence from the feed ----
seeded = False
for root, _, files in os.walk(os.path.join(repo, "tests")):
    for f in files:
        if f.startswith("test") and f.endswith(".py"):
            for body in re.split(r"\n\s*def test_", read(os.path.join(root, f)))[1:]:
                if re.search(r"\.hide\(", body) and re.search(r"feed\(", body) and \
                   re.search(r"assertNotIn|not in\b|assertFalse|assertEqual\(\s*\[\s*\]|==\s*\[\s*\]|assertNotEqual", body):
                    seeded = True

# ---- ANSWER.md ----
bug1_named = bool(re.search(r"\breserved\b", ans_l)) and \
             bool(re.search(r"update_?\s?expression|update_item|updateitem|\bhide\b", ans_l))
near = r"(silent|quiet|drop|absent|missing|omit|strip|ignor|lack|not (returned|included|present|contain|have|in the (result|item|response))|never (sees|returned|present)|left out|without (the )?(field|attribute|it)|comes? back without|no error|empty|none)"
bug2_named = bool(re.search(r"projection", ans_l)) and bool(re.search(r"projection.{0,300}" + near + "|" + near + r".{0,300}projection", ans_l, re.S))
latent_named = bool(re.search(r"\bstatus\b", ans_l)) and bool(re.search(r"archive|condition", ans_l))
blanket_named = bool(re.search(r"(every|all|each|any|blanket|always|convention|rule).{0,80}(alias|expressionattributenames|#)|(alias|expressionattributenames).{0,80}(every|all|each|any|blanket|always|convention)", ans_l, re.S))

cmds = commands(R)
g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"),
  "bug1_named": bug1_named, "bug2_named": bug2_named, "latent_named": latent_named, "blanket_rule_named": blanket_named,
  "bare_reserved_left": bare, "update_bare_hidden_left": update_bare, "projection_bare_left": projection_bare,
  "hidden_check": hidden,
  "bug1_fixed": bool(hidden.get("hide_ok")), "bug2_fixed": bool(hidden.get("feed_ok")),
  "blanket": (not bare) and bool(hidden.get("hide_ok")) and bool(src),
  "seeded_test": seeded, "fixture_tests_pass": tests_pass, "fixture_tests_tail": tests_tail,
  "changed_files": git_changed(repo, base), "commands_issued": len(cmds), "answer_chars": len(ans),
}
g["PASS"] = bug1_named and bug2_named and bool(hidden.get("hide_ok")) and bool(hidden.get("feed_ok")) and bool(hidden.get("visible_ok"))
print(json.dumps(g, indent=1))
