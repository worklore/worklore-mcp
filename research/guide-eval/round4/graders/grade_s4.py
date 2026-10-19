"""s4: what in hearback's current schema isn't in 3NF? Hidden answer key, from reading all 26 migrations
after the 2026-10-10 normal-forms migration (which fixed idea_items.person_id, document_chunks' copies of
its document, documents.is_public, drafts.tokens_in/out, plans.allowed_models):
  A. model_calls (2026-10-15): tokens_in, tokens_out and cost_usd are stored next to `usage` jsonb that
     holds the same numbers; written by the functions, nothing keeps them equal. The same pattern the
     earlier migration fixed on drafts.
  B. code_questions (2026-10-15): usage / cost_usd / steps / model are run totals over its model_calls
     rows (run_id = code_questions.id); kept by hand, no trigger.
  Also acceptable to raise (copies the schema keeps on purpose, guarded by the database):
  C. project_id on child tables (composite foreign keys), D. ideas.asked_by and people.first/last_touch_at
     (triggers), E. jsonb lists (ideas.result_links, code_questions.sources, drafts.meta.resolved) as 1NF.
  False positives: reporting the columns the 10-10 migration dropped as current problems.
PASS = A and B both named, and no dropped column reported as a current problem.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, outside_paths, git_changed, commands

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans = read(os.path.join(repo, "ANSWER.md"))
txt = run_text(R)
src = ans if ans else txt
low = src.lower()

def near(a, b, window=400):
    """a and b occur within `window` chars of each other somewhere in the answer."""
    for m in re.finditer(a, low):
        seg = low[max(0, m.start() - window): m.end() + window]
        if re.search(b, seg): return True
    return False

A = near(r"model_calls", r"tokens_in|tokens_out|cost_usd") and near(r"model_calls", r"usage")
B = near(r"code_questions", r"usage|cost_usd|steps|total|aggregate|sum\b|model_calls|run_id")
C = near(r"project_id", r"cop(y|ies)|redundan|denormal|duplicat|repeated|transitive")
C_guarded = C and near(r"project_id", r"composite|foreign key|\bfk\b|enforce|guard|on purpose|intentional|rls|row level")
D = near(r"asked_by|first_touch_at|last_touch_at", r"cache|derived|count|aggregate|trigger|min\(|max\(")
D_guarded = D and near(r"asked_by|first_touch_at|last_touch_at", r"trigger")
E = near(r"result_links|sources|meta\b|resolved", r"1nf|array|json|repeating|list")
FIXED_MARK = r"dropped|removed|fixed|already|was |were |no longer|previously|normal_forms|2026-10-10|generated|migration 2026|has been"
def false_positive(col, ctx):
    return near(col, ctx) and not near(col, FIXED_MARK)
FP = {
  "idea_items.person_id": false_positive(r"idea_items", r"person_id"),
  "document_chunks copies": false_positive(r"document_chunks", r"\bkind\b|\blabel\b|source_url"),
  "plans.allowed_models": false_positive(r"allowed_models", r"array|1nf|any\s*\("),
  "drafts.tokens_in by hand": false_positive(r"drafts", r"tokens_in") and not near(r"drafts", r"generated"),
}
cmds = commands(R)
db_attempt = [c[:160] for c in cmds if re.search(r"\bpsql\b|supabase (start|db)|pg_dump|postgres://", c)]
tables = sorted(set(re.findall(r"\b(model_calls|code_questions|drafts|items|people|touches|ideas|idea_items|documents|document_chunks|projects|plans|plan_models|founders|accounts|identities|themes|project_memory|voice_samples|source_syncs|sources|waitlist|server_state|knowledge_chunks)\b", low)))
changed = git_changed(repo, base)
g = {
  "answer_file": bool(ans), "answer_chars": len(ans),
  "A_model_calls_derived": A, "B_code_questions_totals": B,
  "C_project_id_copies": C, "C_noted_guarded": C_guarded,
  "D_cached_aggregates": D, "D_noted_trigger": D_guarded,
  "E_jsonb_lists": E,
  "false_positives": {k: v for k, v in FP.items() if v},
  "mentions_kent_or_codd": bool(re.search(r"\bkent\b|\bcodd\b|\bfagin\b", low)),
  "read_functions_dir": any("functions/" in c for c in cmds),
  "db_connection_attempt": db_attempt,
  "tables_named": tables,
  "commands_issued": len(cmds),
  "changed_files": [c for c in changed if c != "ANSWER.md"],
  "outside_paths": outside_paths(R),
}
g["PASS"] = A and B and not g["false_positives"]
print(json.dumps(g, indent=1))
