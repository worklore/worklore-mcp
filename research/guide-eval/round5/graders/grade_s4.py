"""s4: add Cache-Control to a static-site deploy. Hidden answer key (a trap, not a bug):
  The task has an obvious one-liner: `aws s3 cp s3://B/ s3://B/ --recursive --metadata-directive REPLACE
  --cache-control ...`. REPLACE drops every object's Content-Type (it becomes binary/octet-stream) unless
  --content-type is given in the same command; the whole site then downloads instead of rendering.
  Same trap in boto3: copy_object(MetadataDirective="REPLACE") without ContentType.
PASS = the deploy now sets Cache-Control (on upload or on an in-place copy) AND no command/call
       replaces metadata without stating the content type.
Extra: short TTL for html/js, long for assets/ (tiered); existing objects re-tagged, not only future
       uploads; a verify step reading content-type back; invalidation kept.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)
txt = run_text(R)

sources = {}
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d != ".git"]
    for f in files:
        p = os.path.join(root, f)
        if re.search(r"\.(sh|bash|py|js|mjs|ts|yml|yaml|json|toml|Makefile)$", f) or f in ("Makefile", "deploy"):
            sources[os.path.relpath(p, repo)] = read(p)

def shell_commands(s):
    s = "\n".join(l for l in s.splitlines() if not l.lstrip().startswith("#"))  # drop comment lines
    s = re.sub(r"\\\n\s*", " ", s)  # join continuation lines
    return [c.strip() for c in re.split(r"\n|&&|;|\|\|", s)]

trap_hits, cache_set, content_type_explicit, tiered, retag_existing, verify_step, invalidation = [], False, False, False, False, False, False
for name, s in sources.items():
    if name == "ANSWER.md": continue
    for c in shell_commands(s):
        if re.search(r"metadata-directive\s*[= ]\s*REPLACE", c, re.I) and not re.search(r"--content-type", c):
            trap_hits.append(f"{name}: {c[:160]}")
        if re.search(r"--cache-control", c): cache_set = True
        if re.search(r"--content-type", c): content_type_explicit = True
        if re.search(r"--cache-control", c) and re.search(r"s3://[^ ]+\s+s3://", c): retag_existing = True
        if re.search(r"curl\s+-s?I|head-object|HeadObject", c): verify_step = True
        if re.search(r"create-invalidation", c): invalidation = True
    # boto3 / SDK style
    for m in re.finditer(r"MetadataDirective\s*[=:]\s*['\"]REPLACE['\"]", s):
        window = s[max(0, m.start() - 600): m.end() + 600]
        if not re.search(r"ContentType", window):
            trap_hits.append(f"{name}: boto3 REPLACE without ContentType")
    if re.search(r"CacheControl\s*[=:]", s): cache_set = True
    if re.search(r"ContentType\s*[=:]", s): content_type_explicit = True
    ttls = [int(x) for x in re.findall(r"max-age=(\d+)", s)]
    if len(set(ttls)) >= 2: tiered = True

ans_warns = bool(re.search(r"metadata-directive|octet-stream|content[- ]type", ans, re.I))
cmds = commands(R)
aws_run = any(re.search(r"^\s*aws\s+(s3|cloudfront)", c) for c in cmds)

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"), "cache_control_set": cache_set, "trap_hits": trap_hits, "content_type_explicit": content_type_explicit,
  "tiered_ttls": tiered, "retags_existing_objects": retag_existing, "verify_step": verify_step, "invalidation_kept": invalidation,
  "answer_mentions_content_type_or_trap": ans_warns, "aws_cli_executed": aws_run,
  "changed_files": git_changed(repo, base), "commands_issued": len(cmds), "answer_chars": len(ans),
}
g["PASS"] = cache_set and not trap_hits
print(json.dumps(g, indent=1))
