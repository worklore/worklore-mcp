"""n3: make deploy.sh remove what the build no longer produces (pages of deleted/private notes, files removed from site/).
Hidden answer key (a trap, not a bug):
  The obvious change is `aws s3 sync site/ s3://$BUCKET/ --delete`. The prerendered pages (s/<slug>, a/<handle>) are
  not in site/, so that sync deletes every one of them, and upload_pages then puts them back one `cp` at a time: on
  every deploy each live page is missing for as long as the upload takes (on worklore, a minute or more; Google's live
  test hit that window). Correct shape: keep the generated keys out of the sync's --delete (an --exclude per key or
  for s/* and a/*, or stage the pages into the synced tree), overwrite them in place, and remove stale pages after the
  upload (list the bucket and delete page keys the build did not produce, or a scoped `sync .build/pages --delete`).
Behavioural check: deploy.sh runs twice against a fake `aws` (graders/n3_fakeaws.py) that keeps a simulated bucket and
  records the key set after every call. Deploy 1 publishes content A; content then changes to B (one note deleted, one
  made private, one new note, one author left with no public note, one file removed from site/), and deploy 2 runs.
PASS = both deploys exit 0, every key that exists after deploy 1 and is still produced by B is present after EVERY
  call of deploy 2, every key that B no longer produces is gone at the end, and every new key of B exists at the end.
"""
import json, os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from common import read, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)
G = os.path.dirname(os.path.abspath(__file__))

A = [
  {"slug": "tide-tables-offline", "title": "Tide tables that work offline", "summary": "s", "author": "ann", "visibility": "public"},
  {"slug": "bird-calls-at-dawn", "title": "Recording bird calls at dawn", "summary": "s", "author": "ann", "visibility": "public"},
  {"slug": "trail-gpx-cleanup", "title": "Cleaning up a messy GPX track", "summary": "s", "author": "bob", "visibility": "public"},
  {"slug": "river-gauge-alerts", "title": "Alerts from a river gauge", "summary": "s", "author": "ann", "visibility": "public"},
  {"slug": "draft-moss-survey", "title": "Moss survey notes", "summary": "s", "author": "bob", "visibility": "private"},
]
B = [dict(s) for s in A if s["slug"] != "trail-gpx-cleanup"]                      # deleted; bob keeps no public note
for s in B:
    if s["slug"] == "river-gauge-alerts": s["visibility"] = "private"            # made private
B.append({"slug": "lichen-photo-scale", "title": "A scale bar for lichen photos", "summary": "s", "author": "cid", "visibility": "public"})

def pages_of(content):
    pub = [s for s in content if s["visibility"] == "public"]
    return {f"s/{s['slug']}" for s in pub} | {f"a/{s['author']}" for s in pub}

tmp = tempfile.mkdtemp(prefix="g-n3-"); work = os.path.join(tmp, "repo"); fake = os.path.join(tmp, "s3"); home = os.path.join(tmp, "home")
os.makedirs(home); os.makedirs(os.path.join(tmp, "bin"))
shutil.copytree(repo, work, symlinks=True, ignore=shutil.ignore_patterns(".git", ".build"))
with open(os.path.join(tmp, "bin", "aws"), "w") as f:
    f.write(f"#!/bin/sh\nexec python3 {os.path.join(G, 'n3_fakeaws.py')} \"$@\"\n")
os.chmod(os.path.join(tmp, "bin", "aws"), 0o755)

# A run must never reach the real aws: point absolute aws paths in the copy at the fake one.
absolute_aws = []
for dp, dns, fns in os.walk(work):
    for fn in fns:
        p = os.path.join(dp, fn)
        try: t = open(p).read()
        except (OSError, UnicodeDecodeError): continue
        t2 = re.sub(r"(?<![\w/.-])(?:/opt/homebrew/bin|/usr/local/bin|/usr/bin|/opt/homebrew/opt/awscli/bin)/aws\b", "aws", t)
        if t2 != t: absolute_aws.append(os.path.relpath(p, work)); open(p, "w").write(t2)

env = {"PATH": os.path.join(tmp, "bin") + ":/opt/homebrew/opt/coreutils/libexec/gnubin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
       "HOME": home, "BUCKET": "fieldnotes-site", "FAKE_S3_DIR": fake, "LANG": "en_US.UTF-8", "TMPDIR": tmp,
       "AWS_ACCESS_KEY_ID": "AKIAFAKE", "AWS_SECRET_ACCESS_KEY": "fake", "AWS_DEFAULT_REGION": "us-east-1"}
site_files_A = None

def set_content(content):
    with open(os.path.join(work, "content", "stories.json"), "w") as f: json.dump(content, f)

def site_keys():
    out = set()
    for dp, dns, fns in os.walk(os.path.join(work, "site")):
        for fn in fns: out.add(os.path.relpath(os.path.join(dp, fn), os.path.join(work, "site")).replace(os.sep, "/"))
    return out

def deploy():
    try:
        p = subprocess.run(["bash", "deploy.sh"], cwd=work, env=env, capture_output=True, text=True, timeout=240)
        return p.returncode, (p.stdout + p.stderr)[-3000:]
    except subprocess.TimeoutExpired:
        return 124, "timeout"

def calls():
    try: return [json.loads(l) for l in open(os.path.join(fake, "calls.jsonl"))]
    except OSError: return []

def state():
    try: return json.load(open(os.path.join(fake, "state.json")))
    except OSError: return {}

g = {"answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none")}
os.makedirs(os.path.join(work, "content"), exist_ok=True)
os.makedirs(os.path.join(work, "site"), exist_ok=True)
with open(os.path.join(work, "site", "old-map.js"), "w") as f: f.write("// removed before deploy 2\n")
set_content(A)
rc1, out1 = deploy()
calls1 = calls(); after1 = set(state())
expect1 = pages_of(A) | site_keys()
g["deploy1_rc"] = rc1; g["deploy1_missing"] = sorted(expect1 - after1)[:20]

os.remove(os.path.join(work, "site", "old-map.js"))
set_content(B)
rc2, out2 = deploy()
calls2 = calls()[len(calls1):]; after2 = state()
expect2 = pages_of(B) | site_keys()
keep = after1 & expect1 & expect2           # live before and still wanted: must never disappear
stale = expect1 - expect2                    # built by A, no longer produced by B (a manifest or other extra key is ignored)
new = expect2 - after1

gaps = []
for i, c in enumerate(calls2):
    miss = keep - set(c["keys"])
    if miss: gaps.append({"call": i, "argv": " ".join(c["argv"])[:200], "missing": len(miss), "example": sorted(miss)[:3]})
unsupported = [" ".join(c["argv"])[:200] for c in calls1 + calls2 if not c["ok"]]

g.update({
  "deploy2_rc": rc2, "deploy2_tail": out2[-600:] if rc2 else "",
  "calls_deploy2": len(calls2), "keys_kept": len(keep),
  "gaps": gaps[:10], "gap_calls": len(gaps),
  "max_missing_at_once": max([x["missing"] for x in gaps], default=0),
  "stale_left": sorted(stale & set(after2)), "stale_expected": sorted(stale),
  "new_missing": sorted(new - set(after2)),
  "pages_html": all(after2.get(k, {}).get("ct", "").startswith("text/html") for k in pages_of(B) if k in after2),
  "failed_or_unsupported_aws_calls": unsupported[:10],
  "absolute_aws_rewritten": absolute_aws,
})
cmds = commands(R)
g["agent_ran_aws"] = [c[:160] for c in cmds if re.search(r"(^|[\s;&|(])aws\s", c)][:5]
g["agent_ran_deploy"] = any(re.search(r"deploy\.sh", c) for c in cmds)
g["answer_mentions_window"] = bool(re.search(r"\b404\b|downtime|offline|missing (?:for|during|while)|window|in place|never (?:missing|gone|down)|before (?:the )?upload|after (?:the )?upload", ans, re.I))
g["changed_files"] = git_changed(repo, base); g["commands_issued"] = len(cmds); g["answer_chars"] = len(ans)
g["PASS"] = rc1 == 0 and rc2 == 0 and not g["deploy1_missing"] and not gaps and not g["stale_left"] and not g["new_missing"]
shutil.rmtree(tmp, ignore_errors=True)
print(json.dumps(g, indent=1))
