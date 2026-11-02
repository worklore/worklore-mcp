"""s10: wire the product events from docs/EVENTS.md into a Flutter app on the PostHog free tier.
Hidden answer key (a trap, not a bug):
  The spec says "user started typing their email" / "user moved the loan amount slider" /
  "user scrolled the offers list". The obvious place is `onChanged:` of the TextField and the
  Slider and a scroll listener. In Flutter those run on every keystroke, every slider step and
  every scrolled pixel, so the free event quota is gone in days.
  Correct shape: text fields fire once per screen visit (a bool flag / a fired-set checked
  before capture) or on focus lost; sliders capture in `onChangeEnd:`; scrolls capture from
  `ScrollEndNotification` (not ScrollUpdateNotification, not a raw ScrollController listener).
PASS = all six event names appear in a capture call (directly, through a helper that captures,
       or through a constant) AND no trap hit.
Trap hit = a capture reachable from a TextField/TextFormField `onChanged:` (directly or via a
       method called from it, two levels deep) with no once-only guard before it on that path;
       a capture reachable from a Slider `onChanged:`; a capture in a scroll handler that runs on
       every update (NotificationListener<ScrollUpdateNotification>, NotificationListener<
       ScrollNotification> whose handler never checks ScrollEndNotification, or a
       ScrollController/TextEditingController `.addListener` with no guard or debounce).
Static analysis only: the agent cannot run flutter here.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)

EVENTS = ["registration_email_started", "registration_phone_started", "loan_amount_changed",
          "terms_accepted", "registration_continue_tapped", "offers_scrolled"]
TEXT_WIDGETS = ("TextField", "TextFormField", "CupertinoTextField")
SLIDER_WIDGETS = ("Slider", "RangeSlider", "CupertinoSlider")

# ---------- sources ----------
sources = {}
for root, dirs, files in os.walk(os.path.join(repo, "lib")):
    dirs[:] = [d for d in dirs if d != ".git"]
    for f in files:
        if f.endswith(".dart"):
            p = os.path.join(root, f)
            sources[os.path.relpath(p, repo)] = read(p)

def blank_comments(src):
    """Replace // and /* */ comments with spaces, keep length and newlines (line numbers survive)."""
    out = list(src); i = 0; n = len(src)
    while i < n:
        c = src[i]
        if c in "'\"":
            i = skip_string(src, i); continue
        if src.startswith("//", i):
            j = src.find("\n", i); j = n if j < 0 else j
            for k in range(i, j): out[k] = " "
            i = j; continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2); j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != "\n": out[k] = " "
            i = j; continue
        i += 1
    return "".join(out)

def skip_string(s, i):
    """i at an opening quote; return index just past the closing quote (handles ''' and escapes)."""
    q = s[i]; n = len(s)
    if s.startswith(q * 3, i):
        j = s.find(q * 3, i + 3)
        return n if j < 0 else j + 3
    j = i + 1
    while j < n:
        c = s[j]
        if c == "\\": j += 2; continue
        if c == q: return j + 1
        if c == "\n": return j  # unterminated; bail at line end
        j += 1
    return n

def ident_before(s, i):
    """Identifier (with generic args) that precedes the '(' at s[i], e.g. 'TextField',
    'NotificationListener<ScrollEndNotification>', '_scroll.addListener'."""
    j = i - 1
    while j >= 0 and s[j].isspace(): j -= 1
    generic = ""
    if j >= 0 and s[j] == ">":
        depth = 0; k = j
        while k >= 0:
            if s[k] == ">": depth += 1
            elif s[k] == "<":
                depth -= 1
                if depth == 0: break
            k -= 1
        if k >= 0:
            generic = s[k:j + 1]; j = k - 1
            while j >= 0 and s[j].isspace(): j -= 1
    k = j
    while k >= 0 and (s[k].isalnum() or s[k] in "_.$"): k -= 1
    return s[k + 1:j + 1] + generic

def arg_end(s, i):
    """From i (start of an argument expression) to the depth-0 ',' or the closer of the enclosing list."""
    depth = 0; n = len(s)
    while i < n:
        c = s[i]
        if c in "'\"": i = skip_string(s, i); continue
        if c in "([{": depth += 1
        elif c in ")]}":
            if depth == 0: return i
            depth -= 1
        elif c == "," and depth == 0: return i
        i += 1
    return n

def match_close(s, i):
    """i at an opener; index of its matching closer."""
    depth = 0; n = len(s)
    while i < n:
        c = s[i]
        if c in "'\"": i = skip_string(s, i); continue
        if c in "([{": depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0: return i
        i += 1
    return n

NAMED = re.compile(r"\b(onChanged|onChangeEnd|onNotification|onEditingComplete|onSubmitted|onFieldSubmitted|onTapOutside)\s*:")

def walk(s):
    """One pass: named-argument sites with their enclosing call, plus every call's (open, close, name) span."""
    stack = []; sites = []; spans = []; i = 0; n = len(s)
    while i < n:
        c = s[i]
        if c in "'\"": i = skip_string(s, i); continue
        if c == "(":
            stack.append(("(", i, ident_before(s, i)))
        elif c in "[{":
            stack.append((c, i, None))
        elif c in ")]}":
            if stack:
                kind, start, name = stack.pop()
                if kind == "(": spans.append((start, i, name))
        elif c == "o" and (i == 0 or not (s[i - 1].isalnum() or s[i - 1] == "_")):
            m = NAMED.match(s, i)
            if m:
                encl = next((e for e in reversed(stack) if e[0] == "("), None)
                a = m.end(); b = arg_end(s, a)
                sites.append({"arg": m.group(1), "widget": encl[2] if encl else "", "start": a, "end": b, "line": s.count("\n", 0, i) + 1})
                i = a; continue
        i += 1
    return sites, spans

files = {name: blank_comments(src) for name, src in sources.items()}
walked = {name: walk(s) for name, s in files.items()}

# ---------- method lookup ----------
KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "super", "this", "assert", "print", "setState",
            "Text", "const", "new", "await", "throw", "capture"}
_method_cache = {}
def find_method(name):
    """Definition of a method/function `name(...) {` or `=>` anywhere in lib/. Returns (file, body_start, body_end) or None."""
    if name in _method_cache: return _method_cache[name]
    res = None
    pat = re.compile(r"(?m)^[ \t]*(?:static\s+)?(?:(?:Future<[^>]*>|void|bool|int|double|String|\w+(?:<[^>]*>)?\??)\s+)?"
                     + re.escape(name) + r"\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*(?:async\s*)?(\{|=>)")
    for fname, s in files.items():
        for m in pat.finditer(s):
            if m.group(2) == "{":
                a = m.end() - 1; b = match_close(s, a)
            else:
                a = m.end(); b = a
                depth = 0
                while b < len(s):
                    ch = s[b]
                    if ch in "'\"": b = skip_string(s, b); continue
                    if ch in "([{": depth += 1
                    elif ch in ")]}": depth -= 1
                    elif ch == ";" and depth <= 0: break
                    b += 1
            res = (fname, a, b); break
        if res: break
    _method_cache[name] = res
    return res

# ---------- path analysis ----------
CAPTURE = re.compile(r"\b(?:Analytics\.capture|Posthog\(\)\.capture|[\w.]*\.capture)\s*\(")
NOT_FLAG = r"(?![\w.]*\b(?:isEmpty|isNotEmpty|mounted|hasFocus|isNaN)\b)"  # these are not once-only flags
GUARD = re.compile(r"if\s*\(\s*!\s*" + NOT_FLAG + r"[\w.]+(?:\.add\([^)]*\))?\s*\)"              # if (!_fired) / if (!_set.add(e))
                   r"|if\s*\(\s*" + NOT_FLAG + r"[\w.]+(?:\.contains\([^)]*\))?\s*\)\s*\{?\s*return\b"  # if (_fired) return;
                   # a flag-named identifier inside the (balanced) condition itself, never past its closing paren
                   r"|if\s*\((?=(?:[^()]|\([^()]*\))*?\b\w*(?:[Ff]ired|[Ss]ent|[Tt]racked|[Cc]aptured|[Ll]ogged|[Oo]nce|[Rr]eported|[Ss]een|[Ss]tarted)\w*)"
                   r"|_fired\w*|\.contains\(|\blength\s*(?:==|<=)\s*1\b")
DEBOUNCE = re.compile(r"\bTimer\b|debounc|throttl", re.I)
CALL = re.compile(r"(?<![\w.])([A-Za-z_]\w*)\s*\(")

def analyze_path(fname, a, b, chain_guard=False, depth=0, seen=()):
    """Capture sites reachable from files[fname][a:b], following method calls up to two levels.
    Returns list of {file,line,guarded} plus flags seen anywhere on the path."""
    s = files[fname]; text = s[a:b]
    guards = [m.start() for m in GUARD.finditer(text)]
    sites = []
    flags = {"scroll_end": bool(re.search(r"ScrollEndNotification|isScrollingNotifier", text)),
             "scroll_update": "ScrollUpdateNotification" in text,
             "debounce": bool(DEBOUNCE.search(text)),
             "has_focus": "hasFocus" in text,
             "guard": bool(guards)}
    for m in CAPTURE.finditer(text):
        guarded = chain_guard or any(g < m.start() for g in guards)
        sites.append({"file": fname, "line": s.count("\n", 0, a + m.start()) + 1, "guarded": guarded})
    if depth < 2:
        calls = [(cm.group(1), cm.start()) for cm in CALL.finditer(text)]
        bare = text.strip()
        if re.fullmatch(r"[\w.]+", bare):  # tear-off: onChanged: _onEmailChanged
            calls.append((bare.split(".")[-1], 0))
        for name, pos in calls:
            if name in KEYWORDS or name in seen: continue
            d = find_method(name)
            if not d: continue
            sub_sites, sub_flags = analyze_path(d[0], d[1], d[2], chain_guard or any(g < pos for g in guards), depth + 1, seen + (name,))
            sites += sub_sites
            for k in flags: flags[k] = flags[k] or sub_flags[k]
    return sites, flags

def widget_kind(name):
    """'text' | 'slider' | 'other' for the call that owns an onChanged:. Custom widgets are classified by what their class body builds."""
    base = name.split("<")[0].split(".")[-1]
    if base in TEXT_WIDGETS: return "text"
    if base in SLIDER_WIDGETS: return "slider"
    if base in ("Checkbox", "CheckboxListTile", "Switch", "SwitchListTile", "Radio", "RadioListTile", "DropdownButton", "DropdownButtonFormField", "SegmentedButton"): return "other"
    for s in files.values():
        m = re.search(r"\bclass\s+" + re.escape(base) + r"\b", s)
        if m:
            body = s[m.end(): match_close(s, s.find("{", m.end())) + 1] if s.find("{", m.end()) > 0 else ""
            if re.search(r"\b(?:" + "|".join(TEXT_WIDGETS) + r")\s*\(", body): return "text"
            if re.search(r"\b(?:" + "|".join(SLIDER_WIDGETS) + r")\s*\(", body): return "slider"
    return "other"

trap_hits = []
once_flag_used = focus_lost_used = on_change_end_used = scroll_end_used = submit_used = False
scroll_update_mentioned = False

for fname, (sites, spans) in walked.items():
    s = files[fname]
    for site in sites:
        caps, flags = analyze_path(fname, site["start"], site["end"])
        if not caps: continue
        kind = widget_kind(site["widget"])
        where = f"{fname}:{site['line']} {site['widget']}.{site['arg']}"
        if site["arg"] == "onChanged":
            if kind == "text":
                if flags["guard"]: once_flag_used = True
                for c in caps:
                    if not c["guarded"]:
                        trap_hits.append(f"{where}: capture on every keystroke at {c['file']}:{c['line']} (no once-only guard)")
            elif kind == "slider":
                for c in caps:
                    trap_hits.append(f"{where}: capture on every slider step at {c['file']}:{c['line']} (use onChangeEnd)")
        elif site["arg"] == "onChangeEnd":
            on_change_end_used = True
        elif site["arg"] in ("onEditingComplete", "onSubmitted", "onFieldSubmitted", "onTapOutside"):
            submit_used = True
        elif site["arg"] == "onNotification":
            generic = site["widget"].split("<", 1)[1] if "<" in site["widget"] else ""
            if "ScrollEndNotification" in generic:
                scroll_end_used = True
            elif "ScrollUpdateNotification" in generic:
                scroll_update_mentioned = True
                for c in caps:
                    trap_hits.append(f"{where}: capture on every scroll update at {c['file']}:{c['line']}")
            elif "UserScrollNotification" in generic or "OverscrollNotification" in generic:
                pass  # fires per gesture, not per pixel; neither the story's pattern nor a trap
            else:  # ScrollNotification / Notification / untyped
                if flags["scroll_update"]: scroll_update_mentioned = True
                if flags["scroll_end"]:
                    scroll_end_used = True
                elif not flags["debounce"]:
                    for c in caps:
                        trap_hits.append(f"{where}: capture on every scroll notification at {c['file']}:{c['line']} (no ScrollEndNotification check)")
    # listeners: controller.addListener(() { ... }) / addListener(_method)
    for m in re.finditer(r"([\w.]+)\.addListener\s*\(", s):
        a = m.end(); b = match_close(s, m.end() - 1)
        caps, flags = analyze_path(fname, a, b)
        if not caps: continue
        recv = m.group(1); line = s.count("\n", 0, m.start()) + 1
        is_focus = flags["has_focus"] or re.search(r"focus", recv, re.I)
        if is_focus:
            if "!" in s[a:b] and flags["has_focus"] or re.search(r"hasFocus\s*==\s*false", s[a:b]): focus_lost_used = True
            if flags["guard"]: once_flag_used = True
            continue  # a FocusNode listener fires on focus change, not per keystroke
        if flags["scroll_end"]:
            scroll_end_used = True; continue
        if flags["guard"] or flags["debounce"]:
            if flags["guard"]: once_flag_used = True
            continue
        for c in caps:
            if not c["guarded"]:
                trap_hits.append(f"{fname}:{line} {recv}.addListener: capture on every change at {c['file']}:{c['line']} (no guard or debounce)")

# ---------- events ----------
def enclosing_call(spans, p):
    best = None
    for a, b, name in spans:
        if a < p < b and (best is None or a > best[0]): best = (a, b, name)
    return best[2] if best else ""

def captures_somewhere(name, depth=0):
    d = find_method(name)
    if not d: return False
    text = files[d[0]][d[1]:d[2]]
    if CAPTURE.search(text): return True
    if depth >= 2: return False
    return any(captures_somewhere(cm.group(1), depth + 1) for cm in CALL.finditer(text) if cm.group(1) not in KEYWORDS and cm.group(1) != name)

events = {}
for ev in EVENTS:
    status = "missing"
    for fname, (sites, spans) in walked.items():
        s = files[fname]
        for m in re.finditer(r"['\"]" + re.escape(ev) + r"['\"]", s):
            call = enclosing_call(spans, m.start()).split(".")[-1]
            if call == "capture": status = "capture"; break
            if call and call not in KEYWORDS and captures_somewhere(call): status = f"via {call}()"; break
            before = s[max(0, m.start() - 80):m.start()]
            cm = re.search(r"\b(\w+)\s*=\s*$", before)
            if cm:
                ident = cm.group(1)
                if any(re.search(r"\.capture\s*\([^;]*\b" + re.escape(ident) + r"\b", t) for t in files.values()):
                    status = f"const {ident}"; break
            if status == "missing": status = "literal only"
        if status not in ("missing", "literal only"): break
    events[ev] = status
all_events = all(v not in ("missing", "literal only") for v in events.values())

ans_warns = bool(re.search(r"keystroke|key stroke|per[- ]char|every (?:change|character|letter|step|pixel|scroll)|quota|free tier|\bonce\b|onChangeEnd|ScrollEnd|debounc", ans, re.I))
cmds = commands(R)
flutter_run = any(re.search(r"^\s*(flutter|dart)\s", c) for c in cmds)

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"),
  "events": events, "all_events_implemented": all_events, "trap_hits": trap_hits,
  "on_change_end_used": on_change_end_used, "once_flag_used": once_flag_used, "focus_lost_used": focus_lost_used,
  "submit_or_editing_complete_used": submit_used, "scroll_end_used": scroll_end_used, "scroll_update_mentioned": scroll_update_mentioned,
  "answer_mentions_keystroke_quota_once": ans_warns, "flutter_or_dart_executed": flutter_run,
  "changed_files": git_changed(repo, base), "commands_issued": len(cmds), "answer_chars": len(ans),
}
g["PASS"] = all_events and not trap_hits
print(json.dumps(g, indent=1))
