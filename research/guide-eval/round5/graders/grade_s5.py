"""s5: Soft 404 on pages that open fine. Hidden answer key:
  Pages are rendered by app.js from /v1/notes/{slug}. robots.txt has `Disallow: /v1/` (added 2026-09-07
  to stop crawlers hitting POST-only paths). Googlebot obeys robots.txt when rendering, so the fetch is
  blocked, app.js shows the NOT FOUND screen with HTTP 200, and Google files the page as Soft 404.
  The dates line up: pages crawled before Sep 7 stayed indexed. Fix: allow the public read endpoints
  (GET /v1/notes, /v1/notes/{slug}) in robots.txt and keep the per-user/write paths blocked with longer
  rules (Google: longest matching rule wins, Allow wins ties). Alternatives that also fix it: server-side
  rendering of the note content, or moving the API off the blocked prefix. Removing Disallow: /v1/
  entirely also unblocks rendering (counts as fixed, but "per-user paths still blocked" is then false).
PASS = ANSWER.md names robots.txt blocking the API as the cause AND the new robots.txt lets Googlebot
       fetch /v1/notes and /v1/notes/<slug> (or the page no longer depends on that fetch).
Extra: /v1/me and /v1/notes/*/reactions still disallowed; /admin/ still disallowed; a recrawl step named.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)
robots = read(os.path.join(repo, "site", "robots.txt"))
appjs = read(os.path.join(repo, "site", "app.js"))
index = read(os.path.join(repo, "site", "index.html"))
txt = run_text(R)

def rules_for_all(robots):
    """(type, path) rules in the first group that applies to '*' or Googlebot."""
    groups, cur = [], None
    for line in robots.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line: continue
        m = re.match(r"(?i)^([a-z-]+)\s*:\s*(.*)$", line)
        if not m: continue
        k, v = m.group(1).lower(), m.group(2).strip()
        if k == "user-agent":
            if cur is None or cur["rules"]:
                cur = {"agents": [], "rules": []}; groups.append(cur)
            cur["agents"].append(v.lower())
        elif k in ("allow", "disallow") and cur is not None:
            cur["rules"].append((k, v))
    for g in groups:
        if any(a.startswith("googlebot") for a in g["agents"]): return g["rules"]
    for g in groups:
        if "*" in g["agents"]: return g["rules"]
    return []

def match_len(pattern, path):
    if pattern == "": return None
    rx = "^" + "".join(".*" if ch == "*" else ("$" if ch == "$" and i == len(pattern) - 1 else re.escape(ch)) for i, ch in enumerate(pattern))
    return len(pattern) if re.match(rx, path) else None

def allowed(rules, path):
    best, verdict = -1, True
    for kind, pat in rules:
        n = match_len(pat, path)
        if n is None: continue
        if n > best or (n == best and kind == "allow"):
            best, verdict = n, (kind == "allow")
    return verdict

rules = rules_for_all(robots)
paths = {"/v1/notes?limit=50": True, "/v1/notes/soil-ph-kit-review": True, "/v1/notes/soil-ph-kit-review/reactions": False, "/v1/me": False, "/v1/me/drafts": False, "/admin/": False}
verdicts = {p: allowed(rules, p) for p in paths}
public_reads_allowed = verdicts["/v1/notes?limit=50"] and verdicts["/v1/notes/soil-ph-kit-review"]
private_still_blocked = not verdicts["/v1/me"] and not verdicts["/v1/notes/soil-ph-kit-review/reactions"]
admin_still_blocked = not verdicts["/admin/"]
# alternative fix: the page no longer depends on a /v1 fetch to show content
prerendered = bool(re.search(r"<article|<h1>(?!Field notes)", index)) and "fetch(" not in appjs
api_moved = bool(appjs) and "/v1/" not in appjs and "fetch(" in appjs
ans_l = ans.lower()
cause_named = bool(re.search(r"robots\.txt|robots", ans_l)) and bool(re.search(r"/v1|api", ans_l)) and bool(re.search(r"block|disallow|forbid|prevent|can.?t fetch|cannot fetch|not allowed", ans_l))
render_explained = bool(re.search(r"render|javascript|js|fetch", ans_l)) and bool(re.search(r"not found|notfound|empty|error screen|fallback", ans_l))
dates_noted = bool(re.search(r"sep(tember)?\s*7|09-07|2026-09-07", ans_l))
recrawl_named = bool(re.search(r"recrawl|request indexing|url inspection|validate fix|resubmit", ans_l))
longest_match = bool(re.search(r"longest|most specific|specific rule|precedence", ans_l))
cmds = commands(R)
web = bool(re.search(r"WebSearch|WebFetch|web_search|google_web_search|developers\.google\.com", txt))

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"), "robots_changed": "site/robots.txt" in git_changed(repo, base), "rules": rules, "verdicts": verdicts,
  "public_reads_allowed": public_reads_allowed, "private_still_blocked": private_still_blocked, "admin_still_blocked": admin_still_blocked,
  "prerendered_alternative": prerendered, "api_moved_alternative": api_moved,
  "cause_named": cause_named, "render_explained": render_explained, "dates_noted": dates_noted, "recrawl_named": recrawl_named,
  "longest_match_mentioned": longest_match, "web_used": web, "changed_files": git_changed(repo, base), "commands_issued": len(cmds), "answer_chars": len(ans),
}
g["PASS"] = cause_named and (public_reads_allowed or prerendered or api_moved)
print(json.dumps(g, indent=1))
