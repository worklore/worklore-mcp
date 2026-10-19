// POST /functions/v1/ask-code
//   {item_id | project_id, question, check?, draft_text?} → {question: {...status: 'running'}}
//       Asks the project's repo (the ask-code agent, read-only). The answer
//       arrives in the background: read code_questions by id until status is
//       answered or failed.
//   {question_id, use: true} → {question}
//       She used the answer: saved to the project's knowledge (background).
// docs/API.md › ask-code

import { admin, caller, requireMember } from "../_shared/server/ctx.ts";
import { CODE_QUESTION_COLUMNS, startQuestion, useAnswer } from "../_shared/server/ask_code.ts";
import { bad, HttpError, serve, str, uuid } from "../_shared/server/http.ts";

serve(async (req, body) => {
  const c = await caller(req);
  const db = admin();

  if (body.question_id !== undefined) {
    const id = uuid(body.question_id, "question_id")!;
    const { data: q } = await db.from("code_questions").select(CODE_QUESTION_COLUMNS).eq("id", id).maybeSingle();
    if (!q) throw new HttpError(404, "not_found", "No such question.");
    await requireMember(c, q.project_id).catch(() => { throw new HttpError(404, "not_found", "No such question."); });
    if (body.use !== true) return { question: q };
    return { question: await useAnswer(id) };
  }

  const itemId = uuid(body.item_id, "item_id", false) ?? null;
  let projectId = uuid(body.project_id, "project_id", false) ?? null;
  if (itemId) {
    const { data: item } = await db.from("items").select("project_id").eq("id", itemId).maybeSingle();
    if (!item) throw new HttpError(404, "not_found", "No such item.");
    projectId = item.project_id;
  }
  if (!projectId) throw bad("item_id or project_id is required");
  await requireMember(c, projectId).catch(() => { throw new HttpError(404, "not_found", "No such project."); });
  const question = str(body.question, "question", { required: true, max: 2000 })!;
  if (question.trim().length < 3) throw bad("question is too short");
  return {
    question: await startQuestion({
      projectId, itemId, askedBy: c.kind === "user" ? c.userId : null, question,
      checkQuestion: str(body.check, "check", { max: 2000 }) ?? null,
      draftText: str(body.draft_text, "draft_text", { max: 20000 }) ?? null,
    }),
  };
});
