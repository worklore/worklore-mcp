"""s2: PostHog session replay empty on the new UI. Hidden answer key:
  Flutter replay is built from screenshots taken by PostHogWidget. lib/legacy_app.dart wraps its
  MaterialApp in PostHogWidget; lib/new_app.dart (MaterialApp.router) does not, so sessions on the
  new UI have events but no frames. Fix: wrap the new shell's MaterialApp.router in PostHogWidget.
PASS = the file holding MaterialApp.router now has PostHogWidget( before MaterialApp.router( in the
       same build, the legacy wrapper is still there, and ANSWER.md names PostHogWidget.
Extra: explanation mentions screenshots/frames; a comment left in code; analyze run.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)
txt = run_text(R)

def dart_files():
    for root, _, files in os.walk(os.path.join(repo, "lib")):
        for f in files:
            if f.endswith(".dart"): yield os.path.join(root, f)

router_wrapped = False; router_file = None; legacy_wrapped = False
for p in dart_files():
    s = read(p)
    if "MaterialApp.router" in s:
        router_file = os.path.relpath(p, repo)
        # wrapped around MaterialApp.router, or inside its builder: both give replay its frames
        router_wrapped = "PostHogWidget(" in s and "posthog_flutter" in s
    if "class LegacyApp" in s:
        i = s.find("MaterialApp("); j = s.rfind("PostHogWidget(", 0, i)
        legacy_wrapped = j != -1

answer_names_widget = "PostHogWidget" in ans
answer_explains_frames = bool(re.search(r"screenshot|frame|snapshot|capture[sd]? the (widget|screen)", ans, re.I))
comment_left = any("replay" in read(p).lower() and "//" in read(p) and "PostHogWidget" in read(p) for p in dart_files() if "new_app" in p or "MaterialApp.router" in read(p))
cmds = commands(R)
analyze_run = any(re.search(r"\b(flutter|dart)\s+(analyze|pub get|test)", c) for c in cmds)
web = bool(re.search(r"WebSearch|WebFetch|web_search|google_web_search|posthog\.com/docs", txt))

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"), "router_file": router_file, "router_wrapped": router_wrapped, "legacy_still_wrapped": legacy_wrapped,
  "answer_names_PostHogWidget": answer_names_widget, "answer_explains_frames": answer_explains_frames, "comment_left": comment_left,
  "analyze_or_pubget_run": analyze_run, "web_used": web, "changed_files": git_changed(repo, base), "commands_issued": len(cmds),
  "answer_chars": len(ans),
}
g["PASS"] = router_wrapped and legacy_wrapped and answer_names_widget
print(json.dumps(g, indent=1))
