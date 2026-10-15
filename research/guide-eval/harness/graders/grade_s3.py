"""Hidden grader for story 3 (author-local dates), UPDATED for the 2026-10-04 story Verify:
adds (c) a reader in a third timezone sees the same dates and (d) an existing caller that
sends no date still gets the author's local date. The agent never sees this."""
import json, os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from common import read, outside_paths, git_changed

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
g = {"changed_files": git_changed(repo, base)}

probe = r'''
import json, sys, os, inspect
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
sys.path.insert(0, os.getcwd())
import journal
TOKYO, BA, BER = "Asia/Tokyo", "America/Argentina/Buenos_Aires", "Europe/Berlin"
LOCAL = "2026-10-02"
log = []

def freeze(instant):
    for name in ("_utcnow", "_now", "utcnow", "now_utc", "_server_now"):
        if hasattr(journal, name) and callable(getattr(journal, name)):
            setattr(journal, name, lambda instant=instant: instant)

def do_publish(author, tz, instant):
    freeze(instant)
    local = instant.astimezone(ZoneInfo(tz))
    entry = {"author": author, "title": author + " evening", "body": "x"}
    params = list(inspect.signature(journal.publish).parameters)
    kw = {}
    for p in params:
        pl = p.lower()
        if pl in ("entry", "post", "data", "payload"):
            kw[p] = entry
        elif "tz" in pl or "zone" in pl:
            kw[p] = tz
        elif p == "now" or pl in ("server_now", "received_at", "now_utc"):
            kw[p] = instant
        elif "date" in pl:
            kw[p] = local.date().isoformat()
        elif pl in ("client_now", "client_time", "local_time", "client_datetime", "local_now", "authored_at"):
            kw[p] = local
    try:
        post = journal.publish(**kw); shape = "sig:" + ",".join(kw)
    except Exception as e:
        entry2 = dict(entry, date=local.date().isoformat(), local_date=local.date().isoformat())
        kw = {k: (entry2 if v is entry else v) for k, v in kw.items()}
        post = journal.publish(**kw); shape = "entry.date+" + ",".join(kw) + " (first try: %s)" % str(e)[:80]
    log.append(shape)
    return post

def disp(post, viewer):
    n = len(inspect.signature(journal.display_date).parameters)
    try:
        return journal.display_date(post, viewer) if n >= 2 else journal.display_date(post)
    except TypeError:
        return journal.display_date(post)

def authors(fd):
    return [p["author"] if isinstance(p, dict) else getattr(p, "author", str(p)) for p in fd]

def feed():
    try:
        return journal.feed()
    except TypeError:
        return journal.feed(TOKYO)

out = {}
journal.reset()
t = do_publish("yuki", TOKYO, datetime(2026, 10, 2, 14, 30, tzinfo=timezone.utc))   # 23:30 JST
b = do_publish("ana", BA, datetime(2026, 10, 3, 2, 30, tzinfo=timezone.utc))        # 23:30 ART, same evening, later
out["tokyo_author_sees"] = disp(t, TOKYO)
out["ba_author_sees"] = disp(b, BA)
out["a_each_author_sees_own_local_date"] = out["tokyo_author_sees"] == LOCAL and out["ba_author_sees"] == LOCAL
fa = authors(feed())
out["feed"] = fa
out["b_feed_order_matches_submission"] = fa == ["ana", "yuki"]   # contract: newest first
out["x_tokyo_viewer_sees_ba_post"] = disp(b, TOKYO)
out["x_ba_viewer_sees_tokyo_post"] = disp(t, BA)
out["x_date_viewer_independent"] = out["x_tokyo_viewer_sees_ba_post"] == LOCAL and out["x_ba_viewer_sees_tokyo_post"] == LOCAL
THIRD = {"Europe/Berlin": None, "Pacific/Auckland": None}
for z in THIRD:
    THIRD[z] = [disp(t, z), disp(b, z)]
out["c_third_zone_views"] = THIRD
out["c_third_zone_reader_sees_same_dates"] = all(v == [LOCAL, LOCAL] for v in THIRD.values())
# three-zone stress: alphabetical order != submission order, all same local date
journal.reset()
do_publish("yuki", TOKYO, datetime(2026, 10, 2, 14, 30, tzinfo=timezone.utc))
do_publish("zed", BER, datetime(2026, 10, 2, 21, 0, tzinfo=timezone.utc))          # 23:00 CEST
do_publish("ana", BA, datetime(2026, 10, 3, 2, 30, tzinfo=timezone.utc))
out["x3_feed"] = authors(feed())
out["x3_three_zone_order_ok"] = out["x3_feed"] == ["ana", "zed", "yuki"]
out["publish_call_shape"] = log[0]
# legacy call: exactly the original API (entry, client_tz, now=) with no client-supplied date
journal.reset()
try:
    freeze(datetime(2026, 10, 3, 2, 30, tzinfo=timezone.utc))
    try:
        lp = journal.publish({"author": "ana", "title": "t", "body": "x"}, BA, now=datetime(2026, 10, 3, 2, 30, tzinfo=timezone.utc))
    except TypeError as te:
        if "now" not in str(te): raise
        lp = journal.publish({"author": "ana", "title": "t", "body": "x"}, BA)
    out["legacy_ba_author_sees"] = disp(lp, BA)
except Exception as e:
    out["legacy_ba_author_sees"] = "raised: " + type(e).__name__ + ": " + str(e)[:80]
out["x_legacy_api_correct"] = out["legacy_ba_author_sees"] == LOCAL
print(json.dumps(out))
'''
d = tempfile.mkdtemp(prefix="g3-")
rd = os.path.join(d, "r")
shutil.copytree(repo, rd, ignore=shutil.ignore_patterns("__pycache__", ".git"))
with open(os.path.join(rd, "_probe.py"), "w") as f:
    f.write(probe)
p = subprocess.run([sys.executable, "_probe.py"], cwd=rd, capture_output=True, text=True, timeout=60)
try:
    g["scenario"] = json.loads(p.stdout.strip().splitlines()[-1])
except Exception:
    g["scenario"] = {"probe_error": (p.stdout + p.stderr)[-800:]}
sc = g["scenario"]
g["a_each_author_sees_own_local_date"] = bool(sc.get("a_each_author_sees_own_local_date"))
g["b_feed_order_matches_submission"] = bool(sc.get("b_feed_order_matches_submission"))
g["x_date_viewer_independent"] = bool(sc.get("x_date_viewer_independent"))
g["x3_three_zone_order_ok"] = bool(sc.get("x3_three_zone_order_ok"))
g["x_legacy_api_correct"] = bool(sc.get("x_legacy_api_correct"))
g["legacy_ba_author_sees"] = sc.get("legacy_ba_author_sees")
t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=rd, capture_output=True, text=True, timeout=120)
m = re.search(r"Ran (\d+) test", t.stderr + t.stdout)
g["tests_pass"] = t.returncode == 0
g["tests_ran"] = int(m.group(1)) if m else 0
g["outside_paths"] = outside_paths(R)
g["c_third_zone_reader_sees_same_dates"] = bool(sc.get("c_third_zone_reader_sees_same_dates"))
g["c_third_zone_views"] = sc.get("c_third_zone_views")
g["d_existing_caller_no_date_ok"] = g["x_legacy_api_correct"]
g["PASS_old_verify"] = g["a_each_author_sees_own_local_date"] and g["b_feed_order_matches_submission"]
g["PASS"] = g["PASS_old_verify"] and g["c_third_zone_reader_sees_same_dates"] and g["d_existing_caller_no_date_ok"]
print(json.dumps(g, indent=1))
