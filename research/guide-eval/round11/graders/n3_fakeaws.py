"""A fake `aws` CLI for grade_n3.py: one simulated S3 bucket, every call applied atomically and logged.

State lives in $FAKE_S3_DIR: state.json {key: {"ct": content-type, "sha": body hash}}, calls.jsonl (one line per
call: argv, ok, the key set after the call). Supports the s3 commands a deploy script uses (sync, cp, mv, rm, ls),
the common s3api object calls (list-objects[-v2], delete-object(s), put-object, head-object, copy-object), and
no-op cloudfront create-invalidation / sts get-caller-identity. Anything else is logged as unsupported, exit 255.
"""
import fcntl, fnmatch, hashlib, json, mimetypes, os, shutil, sys

D = os.environ["FAKE_S3_DIR"]
STATE = os.path.join(D, "state.json"); LOG = os.path.join(D, "calls.jsonl")
argv = sys.argv[1:]

GLOBAL_VAL = {"--region", "--profile", "--endpoint-url", "--color", "--cli-read-timeout", "--cli-connect-timeout"}
GLOBAL_FLAG = {"--no-cli-pager", "--no-paginate", "--debug", "--no-verify-ssl", "--no-sign-request"}

def strip_globals(a):
    out = []; i = 0
    while i < len(a):
        if a[i] in GLOBAL_VAL: i += 2; continue
        if a[i] in GLOBAL_FLAG: i += 1; continue
        if any(a[i].startswith(g + "=") for g in GLOBAL_VAL): i += 1; continue
        out.append(a[i]); i += 1
    return out

def die(msg, code=255):
    sys.stderr.write(f"fake aws: {msg}\n"); raise SystemExit(code)

def parse(a, value_opts):
    """positional args, {opt: [values]} and bare flags."""
    pos, opts, flags = [], {}, set(); i = 0
    while i < len(a):
        x = a[i]
        if x.startswith("--"):
            if "=" in x:
                k, v = x.split("=", 1); opts.setdefault(k, []).append(v); i += 1; continue
            if x in value_opts:
                if i + 1 >= len(a): die(f"{x} needs a value", 252)
                opts.setdefault(x, []).append(a[i + 1]); i += 2; continue
            flags.add(x); i += 1; continue
        pos.append(x); i += 1
    return pos, opts, flags

def s3url(u):
    if not u.startswith("s3://"): return None
    rest = u[5:]; b, _, k = rest.partition("/")
    return b, k

def guess_ct(path):
    return mimetypes.guess_type(path)[0] or "binary/octet-stream"

def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]

def filtered(rel, filters):
    """aws s3 --exclude/--include: all included by default, later filters win."""
    inc = True
    for kind, pat in filters:
        if fnmatch.fnmatchcase(rel, pat) or fnmatch.fnmatchcase(rel, pat.lstrip("/")):
            inc = (kind == "--include")
    return inc

def filters_of(a):
    out = []; i = 0
    while i < len(a):
        if a[i] in ("--exclude", "--include") and i + 1 < len(a): out.append((a[i], a[i + 1])); i += 2; continue
        if a[i].startswith("--exclude=") or a[i].startswith("--include="):
            k, v = a[i].split("=", 1); out.append((k, v))
        i += 1
    return out

def local_files(root):
    res = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d != ".git"]
        for f in fns:
            p = os.path.join(dp, f); res.append((os.path.relpath(p, root).replace(os.sep, "/"), p))
    return sorted(res)

S3_VAL = {"--exclude", "--include", "--content-type", "--cache-control", "--acl", "--metadata-directive",
          "--storage-class", "--content-encoding", "--content-disposition", "--expires", "--metadata", "--sse",
          "--source-region", "--page-size", "--grants", "--website-redirect", "--content-language"}

def main(state, a):
    out = []
    if not a: die("no command")
    svc = a[0]
    if svc == "sts": out.append(json.dumps({"Account": "000000000000", "Arn": "arn:aws:iam::000000000000:user/ci"})); return out
    if svc == "cloudfront":
        if len(a) > 1 and a[1] == "create-invalidation":
            out.append(json.dumps({"Invalidation": {"Id": "I1", "Status": "InProgress"}})); return out
        die("unsupported cloudfront call")
    if svc == "s3": return s3(state, a[1:], out)
    if svc == "s3api": return s3api(state, a[1:], out)
    die(f"unsupported service {svc}")

def s3(state, a, out):
    if not a: die("s3 needs a subcommand")
    cmd, rest = a[0], a[1:]
    pos, opts, flags = parse(rest, S3_VAL)
    filt = filters_of(rest); dry = "--dryrun" in flags; ct_opt = (opts.get("--content-type") or [None])[-1]
    meta_replace = (opts.get("--metadata-directive") or [""])[-1].upper() == "REPLACE"
    def put(key, path):
        if dry: out.append(f"(dryrun) upload: {path} to s3://B/{key}"); return
        state[key] = {"ct": ct_opt or guess_ct(path), "sha": sha(path)}
    def delete(key):
        if dry: out.append(f"(dryrun) delete: s3://B/{key}"); return
        state.pop(key, None)
    if cmd == "sync":
        if len(pos) != 2: die("sync needs SRC DST", 252)
        src, dst = pos
        if s3url(dst) and not s3url(src):
            _, prefix = s3url(dst); prefix = prefix if (not prefix or prefix.endswith("/")) else prefix + "/"
            if not os.path.isdir(src): die(f"sync source is not a directory: {src}", 2)
            files = [(r, p) for r, p in local_files(src) if filtered(r, filt)]
            seen = set()
            for r, p in files: put(prefix + r, p); seen.add(prefix + r)
            if "--delete" in flags:
                for k in sorted(state):
                    if k.startswith(prefix) and k not in seen and filtered(k[len(prefix):], filt): delete(k)
            return out
        if s3url(src) and not s3url(dst):
            _, prefix = s3url(src); prefix = prefix if (not prefix or prefix.endswith("/")) else prefix + "/"
            os.makedirs(dst, exist_ok=True); seen = set()
            for k in sorted(state):
                if k.startswith(prefix) and filtered(k[len(prefix):], filt):
                    p = os.path.join(dst, k[len(prefix):]); os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
                    if not dry: open(p, "w").write(f"object {k}\n")
                    seen.add(k[len(prefix):])
            if "--delete" in flags and not dry:
                for r, p in local_files(dst):
                    if r not in seen and filtered(r, filt): os.remove(p)
            return out
        die("unsupported sync direction (s3 to s3)")
    if cmd in ("cp", "mv"):
        if len(pos) != 2: die(f"{cmd} needs SRC DST", 252)
        src, dst = pos; rec = "--recursive" in flags
        S, T = s3url(src), s3url(dst)
        if not S and T:
            _, key = T
            if rec:
                prefix = key if (not key or key.endswith("/")) else key + "/"
                for r, p in local_files(src):
                    if filtered(r, filt): put(prefix + r, p)
                    if cmd == "mv" and not dry: os.remove(p)
                return out
            if src == "-": die("stdin upload not supported")
            if not os.path.isfile(src): die(f"The user-provided path {src} does not exist.", 255)
            if not key or key.endswith("/"): key = key + os.path.basename(src)
            put(key, src)
            if cmd == "mv" and not dry: os.remove(src)
            return out
        if S and T:  # s3 to s3: copies in place or elsewhere; metadata pass
            _, skey = S; _, tkey = T
            if rec:
                sp = skey if (not skey or skey.endswith("/")) else skey + "/"
                tp = tkey if (not tkey or tkey.endswith("/")) else tkey + "/"
                for k in sorted(list(state)):
                    if k.startswith(sp) and filtered(k[len(sp):], filt):
                        obj = dict(state[k])
                        if ct_opt: obj["ct"] = ct_opt
                        elif meta_replace: obj["ct"] = "binary/octet-stream"
                        if not dry:
                            state[tp + k[len(sp):]] = obj
                            if cmd == "mv" and tp + k[len(sp):] != k: state.pop(k, None)
                return out
            if skey not in state: die(f"An error occurred (404) when calling the HeadObject operation: Key \"{skey}\" does not exist", 1)
            obj = dict(state[skey])
            if ct_opt: obj["ct"] = ct_opt
            elif meta_replace: obj["ct"] = "binary/octet-stream"
            if not dry:
                state[tkey] = obj
                if cmd == "mv" and tkey != skey: state.pop(skey, None)
            return out
        if S and not T:  # download
            _, skey = S
            if rec:
                sp = skey if (not skey or skey.endswith("/")) else skey + "/"
                for k in sorted(state):
                    if k.startswith(sp) and filtered(k[len(sp):], filt):
                        p = os.path.join(dst, k[len(sp):]); os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
                        open(p, "w").write(f"object {k}\n")
                return out
            if skey not in state: die(f"An error occurred (404) when calling the HeadObject operation: Not Found", 1)
            p = dst if dst != "-" else None
            if p is None: out.append(f"object {skey}"); return out
            if os.path.isdir(p): p = os.path.join(p, os.path.basename(skey))
            open(p, "w").write(f"object {skey}\n"); return out
        die("cp between two local paths")
    if cmd == "rm":
        if len(pos) != 1 or not s3url(pos[0]): die("rm needs one s3:// path", 252)
        _, key = s3url(pos[0])
        if "--recursive" in flags:
            sp = key if (not key or key.endswith("/")) else key + "/"
            for k in sorted(list(state)):
                if k.startswith(sp) and filtered(k[len(sp):], filt): delete(k)
        else:
            delete(key)
        return out
    if cmd == "ls":
        if not pos: out.append("2026-01-01 00:00:00 fieldnotes-site"); return out
        _, key = s3url(pos[0])
        if "--recursive" in flags:
            for k in sorted(state):
                if k.startswith(key): out.append(f"2026-11-01 12:00:00       1024 {k}")
            return out
        sp = key if (not key or key.endswith("/")) else key + "/"
        if key and key in state and not key.endswith("/"):
            out.append(f"2026-11-01 12:00:00       1024 {os.path.basename(key)}"); return out
        dirs = set()
        for k in sorted(state):
            if k.startswith(sp):
                r = k[len(sp):]
                if "/" in r: dirs.add(r.split("/", 1)[0])
                else: out.append(f"2026-11-01 12:00:00       1024 {r}")
        for d in sorted(dirs): out.insert(0, f"                           PRE {d}/")
        return out
    if cmd in ("mb", "rb", "website", "presign"):
        die(f"s3 {cmd} not allowed here")
    die(f"unsupported s3 command {cmd}")

API_VAL = {"--bucket", "--key", "--prefix", "--query", "--output", "--delete", "--body", "--content-type",
           "--cache-control", "--max-items", "--start-after", "--copy-source", "--metadata-directive",
           "--continuation-token", "--delimiter", "--page-size", "--starting-token", "--max-keys", "--acl"}

def render(data, opts):
    q = (opts.get("--query") or [None])[-1]; fmt = (opts.get("--output") or ["json"])[-1]
    if q:
        import jmespath
        data = jmespath.search(q, data)
    if fmt == "text":
        if data is None: return ["None"]
        if isinstance(data, list):
            if data and all(isinstance(x, list) for x in data): return ["\t".join(map(str, x)) for x in data]
            if data and all(isinstance(x, dict) for x in data): return ["\t".join(map(str, x.values())) for x in data]
            return ["\t".join(map(str, data))]
        if isinstance(data, dict): return ["\t".join(map(str, data.values()))]
        return [str(data)]
    return [json.dumps(data, indent=4)]

def s3api(state, a, out):
    if not a: die("s3api needs an operation")
    op, rest = a[0], a[1:]
    pos, opts, flags = parse(rest, API_VAL)
    def one(k): return (opts.get(k) or [None])[-1]
    if op in ("list-objects-v2", "list-objects"):
        prefix = one("--prefix") or ""
        keys = [k for k in sorted(state) if k.startswith(prefix)]
        if one("--start-after"): keys = [k for k in keys if k > one("--start-after")]
        data = {"Contents": [{"Key": k, "Size": 1024, "LastModified": "2026-11-01T12:00:00+00:00"} for k in keys]} if keys else {}
        if "Contents" not in data and one("--query") and (one("--output") or "json") == "json":
            out.append("null"); return out
        out.extend(render(data, opts)); return out
    if op == "delete-object":
        state.pop(one("--key"), None); out.append("{}"); return out
    if op == "delete-objects":
        spec = one("--delete") or ""
        if spec.startswith("file://"): spec = open(spec[7:]).read()
        try:
            objs = json.loads(spec)["Objects"]; keys = [o["Key"] for o in objs]
        except Exception:
            import re
            keys = re.findall(r"Key=([^,}\]]+)", spec)
        for k in keys: state.pop(k.strip().strip('"'), None)
        out.append(json.dumps({"Deleted": [{"Key": k} for k in keys]})); return out
    if op == "put-object":
        body = one("--body"); key = one("--key")
        state[key] = {"ct": one("--content-type") or "binary/octet-stream", "sha": sha(body) if body and os.path.isfile(body) else "empty"}
        out.append(json.dumps({"ETag": "\"x\""})); return out
    if op == "head-object":
        k = one("--key")
        if k not in state: die("An error occurred (404) when calling the HeadObject operation: Not Found", 254)
        out.extend(render({"ContentType": state[k]["ct"], "ContentLength": 1024}, opts)); return out
    if op == "copy-object":
        src = one("--copy-source") or ""; _, _, skey = src.partition("/")
        if skey not in state: die("NoSuchKey", 254)
        obj = dict(state[skey])
        if one("--content-type"): obj["ct"] = one("--content-type")
        elif (one("--metadata-directive") or "").upper() == "REPLACE": obj["ct"] = "binary/octet-stream"
        state[one("--key")] = obj; out.append("{}"); return out
    die(f"unsupported s3api operation {op}")

os.makedirs(D, exist_ok=True)
with open(os.path.join(D, "lock"), "w") as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    a = strip_globals(argv); ok = True; out = []; code = 0
    try:
        out = main(state, a)
    except SystemExit as e:
        ok = False; code = e.code if isinstance(e.code, int) else 255
    json.dump(state, open(STATE + ".tmp", "w")); os.replace(STATE + ".tmp", STATE)
    with open(LOG, "a") as f:
        f.write(json.dumps({"argv": argv, "ok": ok, "code": code, "keys": sorted(state)}) + "\n")
if out: print("\n".join(out))
sys.exit(code)
