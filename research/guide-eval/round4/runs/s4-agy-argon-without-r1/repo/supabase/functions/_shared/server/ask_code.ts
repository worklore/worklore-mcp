// Ask the code: a question about the project's linked repo (projects.
// github_repo), answered by the ask-code agent (askcode/agent.ts) through
// the Hearback.dev installation. The row is created at once (running) and
// answered in the background; the app polls code_questions. Every step is
// a model_calls row (purpose ask_code, run_id = the question).
//
// Limits: ASK_CODE_DAILY_CAP questions a day across projects (default 25),
// and per run ASK_CODE_MAX_STEPS (12), ASK_CODE_MAX_USD (1.00), a 2-minute
// deadline. Model: ASK_CODE_MODEL (default claude-opus-5-5), effort
// ASK_CODE_EFFORT (medium).
//
// Used answers (she put one in her reply) go to the project's knowledge as
// background (never quoted or linked), so later drafts know the fact.

import { anthropicSender, askCode, AskRun } from "../askcode/agent.ts";
import { RepoTools } from "../askcode/repo_tools.ts";
import { githubApp } from "../connectors/github/app.ts";
import { admin, background, env } from "./ctx.ts";
import { installationForRepo } from "./github.ts";
import { HttpError } from "./http.ts";
import { storeDocs } from "./knowledge.ts";
import { withinBudget } from "./models.ts";
import { currentUsage, logModelCall, withUsage } from "./usage.ts";

export const CODE_QUESTION_COLUMNS =
  "id, project_id, item_id, question, check_question, repo, commit_sha, status, answered_by, answer, details, sources, confidence, model, steps, cost_usd, error, created_at, answered_at, used_at";

/** Pure: what the agent reads about the conversation (the comment, the thread's end, her draft). */
export function conversationContext(item: { text?: string | null; thread?: { author?: string; text?: string }[] | null; my_post?: { title?: string } | null } | null, draft?: string | null): string {
  if (!item) return draft?.trim() ? `Her draft reply:\n${draft.trim()}` : "";
  const lines: string[] = [];
  if (item.my_post?.title) lines.push(`Her post: ${item.my_post.title}`);
  for (const m of (item.thread ?? []).slice(-3)) if (m?.text) lines.push(`${m.author ?? "someone"}: ${m.text.slice(0, 600)}`);
  if (item.text) lines.push(`The comment she is answering: ${item.text.slice(0, 1500)}`);
  if (draft?.trim()) lines.push(`Her draft reply:\n${draft.trim().slice(0, 2000)}`);
  return lines.join("\n");
}

export async function startQuestion(o: {
  projectId: string; itemId?: string | null; askedBy?: string | null;
  question: string; checkQuestion?: string | null; draftText?: string | null;
}) {
  const db = admin();
  const { data: project, error } = await db.from("projects").select("github_repo").eq("id", o.projectId).single();
  if (error) throw error;
  const repo = project?.github_repo as string | null;
  if (!repo) throw new HttpError(409, "no_repo", "Link the project's GitHub repo first (Project › GitHub).");
  const app = githubApp();
  const reach = app ? await installationForRepo(o.projectId, repo, app) : null;
  if (!app || !reach) {
    throw new HttpError(409, "repo_not_installed", `Hearback.dev can't read ${repo}. Install it on the repo (Project › GitHub › Connect).`);
  }
  if (!env("ANTHROPIC_API_KEY")) throw new HttpError(503, "not_configured", "Ask the code isn't set up on the server.");
  if (!await withinBudget("ask_code", Number(env("ASK_CODE_DAILY_CAP") ?? 25))) {
    throw new HttpError(429, "daily_limit", "That's today's limit for Ask the code. Try again tomorrow.");
  }
  let item = null;
  if (o.itemId) {
    const { data } = await db.from("items").select("text, thread, my_post").eq("id", o.itemId).maybeSingle();
    item = data;
  }
  const { data: row, error: e2 } = await db.from("code_questions").insert({
    project_id: o.projectId, item_id: o.itemId ?? null, asked_by: o.askedBy ?? null,
    question: o.question.trim(), check_question: o.checkQuestion?.trim() || null, repo: reach.repo.full_name,
  }).select(CODE_QUESTION_COLUMNS).single();
  if (e2) throw e2;
  const context = conversationContext(item, o.draftText);
  background(withUsage({ ...currentUsage(), run_id: row.id, item_id: o.itemId ?? null }, () =>
    answerQuestion(row.id, { repo: reach.repo.full_name, branch: reach.repo.default_branch, installationId: reach.installation.installation_id, question: row.question, context })));
  return row;
}

async function answerQuestion(id: string, o: { repo: string; branch: string | null; installationId: number; question: string; context: string }) {
  const db = admin();
  const app = githubApp()!;
  try {
    const get = <T>(path: string) => app.asInstallation<T>(o.installationId, "GET", path);
    const head = await get<{ sha: string }>(`/repos/${o.repo}/commits/${encodeURIComponent(o.branch ?? "HEAD")}`);
    await db.from("code_questions").update({ commit_sha: head.sha }).eq("id", id);
    const model = env("ASK_CODE_MODEL") ?? "claude-opus-5-5";
    const run: AskRun = await askCode({ question: o.question, repo: o.repo, context: o.context }, new RepoTools(o.repo, head.sha, get), {
      model,
      effort: (env("ASK_CODE_EFFORT") ?? "medium") as "low" | "medium" | "high",
      maxSteps: Number(env("ASK_CODE_MAX_STEPS") ?? 12),
      maxUsd: Number(env("ASK_CODE_MAX_USD") ?? 1),
      deadlineMs: 120_000,
      send: anthropicSender(env("ANTHROPIC_API_KEY")!),
      onStep: (s) => logModelCall({
        purpose: "ask_code", provider: "anthropic", model: s.model, ok: s.ok, error: s.error,
        tokens_in: s.input + s.cache_read + s.cache_write, tokens_out: s.output,
        usage: { input: s.input, output: s.output, cache_read: s.cache_read, cache_write: s.cache_write, cost_usd: s.cost_usd },
        cost_usd: s.cost_usd, latency_ms: s.latency_ms,
      }),
    });
    await db.from("code_questions").update({
      status: "answered", answer: run.answer, details: run.details, sources: run.sources, confidence: run.confidence,
      model: run.model, steps: run.steps, cost_usd: run.usage.cost_usd,
      usage: { ...run.usage, tool_calls: run.tool_calls, github_requests: run.github_requests },
      answered_at: new Date().toISOString(),
    }).eq("id", id);
  } catch (e) {
    const msg = (e as Error).message ?? String(e);
    console.error(`ask-code ${id} failed:`, msg.slice(0, 300));
    const { data: steps } = await db.from("model_calls").select("cost_usd").eq("run_id", id);
    const spent = (steps ?? []).reduce((a, r) => a + Number(r.cost_usd ?? 0), 0);
    await db.from("code_questions").update({ status: "failed", error: msg.slice(0, 300), cost_usd: spent }).eq("id", id);
  }
}

/** She used the answer: it becomes background knowledge for later drafts. */
export async function useAnswer(id: string) {
  const db = admin();
  const { data: q, error } = await db.from("code_questions").select(CODE_QUESTION_COLUMNS).eq("id", id).maybeSingle();
  if (error) throw error;
  if (!q) throw new HttpError(404, "not_found", "No such question.");
  if (q.status !== "answered" || !q.answer) throw new HttpError(409, "not_answered", "That question has no answer yet.");
  if (!q.used_at) {
    const files = (q.sources as { path: string }[]).map((s) => s.path);
    await storeDocs(q.project_id, [{
      source: "ask_code",
      doc: {
        kind: "fact",
        title: q.question.slice(0, 200),
        url: `hearback:code-answer/${q.id}`,
        published_at: (q.answered_at ?? q.created_at).slice(0, 10),
        markdown: [`Q: ${q.question}`, `A: ${q.answer}`, q.details ?? "", files.length ? `(From ${q.repo}: ${files.join(", ")})` : ""].filter(Boolean).join("\n\n"),
        label: "background",
      },
    }]);
    const { data } = await db.from("code_questions").update({ used_at: new Date().toISOString() }).eq("id", id).select(CODE_QUESTION_COLUMNS).single();
    return data;
  }
  return q;
}
