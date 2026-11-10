"""A stand-in `codex` for grade_n4.py: `codex exec ... --json [-o FILE] PROMPT` prints a short JSON event stream ending in
an agent_message with the grader's nonce, and writes that message to the -o file. Under the stub sandbox
(SANDBOX_STUB_RULES set), a write the profile denies fails the way Codex CLI 0.160 fails under the real sandbox-exec:
'Failed to write last message file "<path>": Operation not permitted (os error 1)' on stderr, and exit code 0."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from n4_stub_sandbox import allowed

a = sys.argv[1:]
VAL = {"-o", "--output-last-message", "-C", "--cd", "-m", "--model", "-c", "--config", "-s", "--sandbox", "-p",
       "--profile", "--color", "-i", "--image", "--output-schema", "--add-dir"}
out_file = None; cd = os.getcwd(); pos = []; i = 0
while i < len(a):
    x = a[i]
    if x in VAL:
        v = a[i + 1] if i + 1 < len(a) else ""
        if x in ("-o", "--output-last-message"): out_file = v
        if x in ("-C", "--cd"): cd = v
        i += 2; continue
    if x.startswith("--output-last-message="): out_file = x.split("=", 1)[1]; i += 1; continue
    if x.startswith("-"): i += 1; continue
    pos.append(x); i += 1
rules = json.loads(os.environ["SANDBOX_STUB_RULES"]) if os.environ.get("SANDBOX_STUB_RULES") else None
msg = "STUB-FINAL " + os.environ.get("N4_NONCE", "")
if rules is not None and not allowed(cd, rules, write=False):
    sys.stderr.write(f"Error: failed to read {cd}: Operation not permitted (os error 1)\n"); sys.exit(1)
for ev in ({"type": "thread.started", "thread_id": "stub"}, {"type": "turn.started"},
           {"type": "item.completed", "item": {"id": "item_1", "type": "agent_message", "text": msg}},
           {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}}):
    print(json.dumps(ev)); sys.stdout.flush()
written = False
if out_file:
    if rules is not None and not allowed(os.path.abspath(out_file), rules, write=True):
        sys.stderr.write(f'Failed to write last message file "{os.path.abspath(out_file)}": Operation not permitted (os error 1)\n')
    else:
        try:
            with open(out_file, "w") as f: f.write(msg + "\n")
            written = True
        except OSError as e:
            sys.stderr.write(f'Failed to write last message file "{out_file}": {e.strerror} (os error {e.errno})\n')
log = os.environ.get("N4_LOG")
if log:
    with open(os.path.join(log, "codex.jsonl"), "a") as f:
        f.write(json.dumps({"argv": a, "under_sandbox": rules is not None, "out_file": out_file, "written": written,
                            "cwd": os.getcwd(), "codex_home": os.environ.get("CODEX_HOME")}) + "\n")
sys.exit(0)
