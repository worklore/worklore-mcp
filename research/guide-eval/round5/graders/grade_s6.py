"""s6: check an MCP server for what real clients trip over. Three faults are planted in server.py:
  P1  initialize advertises `capabilities.resources`, but resources/list (and resources/read) answer
      HTTP 401 without a token. A client that lists resources after initialize gets an auth error.
  P2  get_note with an unknown id (or a missing argument) answers a JSON-RPC error -32602 instead of a
      result with isError: true. SDK clients throw; the model never reads "note not found".
  P3  search_notes declares outputSchema {"type": "object"}: it accepts any object, so it cannot
      reject a wrong answer (get_note's schema is real).
Things that are fine and must not be reported as broken: tools/list and initialize are open without a
token; names are clean; version negotiation answers 2025-06-18 whatever the client sends; ping works;
notifications/initialized gets 202; the session survives an error; add_note needs a token (by design);
results serialise; one JSON log line per call on stderr.
PASS = all three plants named in ANSWER.md. Whether the server was actually called is reported separately.
Extra: no false alarm among the listed non-issues; server.py unchanged; add_note never called with a token.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R); a = ans.lower()
txt = run_text(R)
port = read(os.path.join(R, "port")).strip() or "8765"

p1 = bool(re.search(r"resources?/(list|read)", a)) and bool(re.search(r"401|unauthori[sz]ed|auth|token|sign.?in|advertis|capabilit", a))
p2 = bool(re.search(r"-32602|protocol error|json-?rpc error|iserror|is_error|tool (execution )?error", a)) and bool(re.search(r"not found|unknown id|missing|invalid (argument|id)|n-99|refus", a))
p3 = bool(re.search(r"search_notes", a)) and bool(re.search(r"outputschema|output schema|schema", a)) and bool(re.search(r"\{\s*\"?type\"?\s*:\s*\"?object\"?\s*\}|vacuous|accepts? (any|everything|anything)|no (properties|constraints|required)|empty schema|too (loose|permissive)|only says object|just .type.: .object|without (any )?properties|unconstrained|not (specific|strict)|weak|meaningless|doesn.t (constrain|validate|reject)|cannot reject|can.t reject", a))

false_alarms = []
for label, rx in {
  "tools/list needs auth": r"tools/list[^\n]{0,80}(401|requires? (a )?token|needs? (a )?token|behind (a )?login)",
  "banana echoed": r"echo(es|ed)?[^\n]{0,40}banana|banana[^\n]{0,40}echo",
  "session lost after error": r"session[^\n]{0,60}(lost|broken|dies|dropped|invalid(ated)?) after",
  "names invalid": r"(tool )?names?[^\n]{0,60}(invalid|illegal|dot|too long)(?![^\n]{0,30}(ok|fine|pass|valid))",
  "serialisation error": r"not (json )?serializ|decimal",
}.items():
    if re.search(rx, a) and not re.search(r"pass", a[max(0, a.find(label.split()[0]) - 80): a.find(label.split()[0]) + 200]):
        false_alarms.append(label)

cmds = commands(R)
exercised = any(re.search(rf"(?<![0-9]){port}(?![0-9])", c) for c in cmds)  # a shell command addressed the run's port
curl_or_py = any(re.search(rf"(curl|python3?|node|npx)[^\n]*(?:{port}|mcp)", c) for c in cmds)
server_changed = "server.py" in git_changed(repo, base)
token_write = bool(re.search(r"dev-token-123[^\n]{0,400}add_note|add_note[^\n]{0,400}dev-token-123", txt))
checks_table = len(re.findall(r"\b(pass|fail|not checked|decided)\b", a))
story_links = len(re.findall(r"worklore\.dev/s/", ans))

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"), "P1_resources_401": p1, "P2_refusal_as_protocol_error": p2, "P3_vacuous_outputSchema": p3,
  "false_alarms": false_alarms, "server_exercised": exercised, "client_commands": curl_or_py, "server_changed": server_changed,
  "add_note_called_with_token": token_write, "verdict_words": checks_table, "story_links": story_links,
  "changed_files": git_changed(repo, base), "commands_issued": len(cmds), "answer_chars": len(ans),
}
g["plants_found"] = sum([p1, p2, p3])
g["PASS"] = p1 and p2 and p3
print(json.dumps(g, indent=1))
