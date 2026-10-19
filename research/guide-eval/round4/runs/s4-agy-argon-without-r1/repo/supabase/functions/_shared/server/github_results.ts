// What happened to an idea's issue, and the follow-up replies it earns.
// docs/ARCHITECTURE.md › GitHub App › Results.
//
//   checkIdea     reads the issue (state, closing PRs, last maintainer comment,
//                 the linked board's Status) and stores it on the idea
//   shareResult   one share_result draft per person who asked (never posted)
//   sweep         github-results' cron run: checks open issues, and when one is
//                 done, drafts the follow-ups on its own

import { githubApp, GithubApp } from "../connectors/github/app.ts";
import { ISSUE_RESULT, IssueResult, outcome, readIssueResult, ResultLink, resultForDraft } from "../connectors/github/boards.ts";
import { makeDraft } from "../core/draft_run.ts";
import { admin, projectFounder } from "./ctx.ts";
import { installationForRepo } from "./github.ts";
import { HttpError } from "./http.ts";

export interface WatchedIdea {
  id: string; project_id: string; title: string; status: string;
  github_issue_number: number | null; github_issue_repo: string | null;
  github_issue_state: string | null; github_checked_at: string | null;
  result_note: string | null; result_links: ResultLink[] | null; result_drafted_at: string | null;
}

export const WATCH_COLUMNS = "id, project_id, title, status, github_issue_number, github_issue_repo, github_issue_state, " +
  "github_checked_at, result_note, result_links, result_drafted_at";

/** Done issues closed longer ago than this get no automatic drafts (she drafts them from the idea). */
export const AUTO_DRAFT_WINDOW_MS = 30 * 24 * 3600_000;
/** People who get a follow-up per idea. */
export const MAX_FOLLOWUPS = 10;

/**
 * Pure. The idea's new status for an outcome: done → done, dropped (not
 * planned) → not_now, open → issue_open. Her own "not now" on an idea whose
 * issue is still open stays.
 */
export function ideaStatusFor(current: string, o: "done" | "dropped" | "open"): string {
  if (o === "done") return "done";
  if (o === "dropped") return "not_now";
  return current === "done" ? "issue_open" : current; // reopened
}

/** Reads the issue from GitHub and stores what happened on the idea. Null when the app can't reach the repo. */
export async function checkIdea(idea: WatchedIdea, app: GithubApp | null = githubApp()):
  Promise<{ result: IssueResult; outcome: "done" | "dropped" | "open"; idea: WatchedIdea } | null> {
  if (!app || !idea.github_issue_number || !idea.github_issue_repo) return null;
  const db = admin();
  const reach = await installationForRepo(idea.project_id, idea.github_issue_repo, app);
  if (!reach) return null;
  const { data: project } = await db.from("projects").select("github_board_id").eq("id", idea.project_id).single();
  const [owner, name] = reach.repo.full_name.split("/");
  const { data } = await app.graphql(reach.installation.installation_id, ISSUE_RESULT, { owner, name, number: idea.github_issue_number });
  const result = readIssueResult(data, project?.github_board_id ?? null);
  if (!result) throw new HttpError(404, "issue_not_found", `Issue #${idea.github_issue_number} isn't in ${reach.repo.full_name} any more.`);
  const o = outcome(result);
  // Her edited note wins over GitHub's comment; links are merged (hers first).
  const links = mergeLinks(idea.result_links ?? [], result.links);
  const patch = {
    github_issue_state: result.state, github_issue_state_reason: result.reason, github_issue_closed_at: result.closed_at,
    github_board_status: result.board_status, github_checked_at: new Date().toISOString(),
    result_note: idea.result_note ?? result.note, result_note_url: result.note_url, result_links: links,
    status: ideaStatusFor(idea.status, o), updated_at: new Date().toISOString(),
  };
  const { data: updated, error } = await db.from("ideas").update(patch).eq("id", idea.id).select(WATCH_COLUMNS).single();
  if (error) throw error;
  return { result, outcome: o, idea: updated as unknown as WatchedIdea };
}

/** Pure. Links by URL, first spelling wins, ≤ 8. */
export function mergeLinks(a: ResultLink[], b: ResultLink[]): ResultLink[] {
  const seen = new Set<string>();
  return [...a, ...b].filter((l) => l?.url && !seen.has(l.url.toLowerCase()) && seen.add(l.url.toLowerCase())).slice(0, 8);
}

export interface FollowUp { item_id: string; person_id: string; draft_id: string | null; error?: string }

/**
 * One share_result draft per person who asked (their latest message on this
 * idea), in the founder's voice. Marks the idea done and drafted. Never posts.
 */
export async function shareResult(ideaId: string, opts: { founderId?: string | null; requestedBy?: string | null }): Promise<{ followups: FollowUp[] }> {
  const db = admin();
  const { data: idea } = await db.from("ideas").select(WATCH_COLUMNS).eq("id", ideaId).maybeSingle();
  if (!idea) throw new HttpError(404, "not_found", "No such idea.");
  const w = idea as unknown as WatchedIdea;
  if (!w.result_note?.trim() && !(w.result_links ?? []).length) {
    throw new HttpError(422, "no_result", "There's nothing to tell them yet: add what was done or a link first.");
  }
  const { data: rows, error } = await db.from("idea_items")
    .select("item_id, items(id, person_id, status, posted_at)").eq("idea_id", ideaId);
  if (error) throw error;
  // The latest message per person; spam and hidden items get nothing.
  const latest = new Map<string, { id: string; person_id: string; posted_at: string | null }>();
  for (const r of (rows ?? []) as unknown as { items: { id: string; person_id: string; status: string; posted_at: string | null } | null }[]) {
    const it = r.items;
    if (!it || it.status === "skipped") continue;
    const had = latest.get(it.person_id);
    if (!had || (it.posted_at ?? "") > (had.posted_at ?? "")) latest.set(it.person_id, it);
  }
  const text = resultForDraft({ note: w.result_note, links: w.result_links ?? [] }, w.title);
  const founderId = opts.founderId ?? await projectFounder(w.project_id);
  const followups: FollowUp[] = [];
  for (const it of [...latest.values()].slice(0, MAX_FOLLOWUPS)) {
    try {
      const d = await makeDraft(it.id, { founderId, requestedBy: opts.requestedBy ?? null, intent: "share_result", result: text, length: "full" });
      followups.push({ item_id: it.id, person_id: it.person_id, draft_id: d.draft_id });
    } catch (e) {
      console.error("share_result:", (e as Error).message.slice(0, 160));
      followups.push({ item_id: it.id, person_id: it.person_id, draft_id: null, error: (e as Error).message.slice(0, 160) });
    }
  }
  if (followups.some((f) => f.draft_id)) {
    await db.from("ideas").update({ status: "done", result_drafted_at: new Date().toISOString(), updated_at: new Date().toISOString() }).eq("id", ideaId);
  }
  return { followups };
}

/** Ideas re-checked per cron run, and how often an open issue is re-read. */
const SWEEP_LIMIT = 40;
const RECHECK_OPEN_MS = 15 * 60_000;
const RECHECK_CLOSED_MS = 24 * 3600_000;

/** Pure. Is this idea due for a check (open issues often, closed-not-done ones daily)? */
export function due(i: Pick<WatchedIdea, "github_checked_at" | "github_issue_state">, now = Date.now()): boolean {
  if (!i.github_checked_at) return true;
  const age = now - Date.parse(i.github_checked_at);
  return age >= (i.github_issue_state === "closed" ? RECHECK_CLOSED_MS : RECHECK_OPEN_MS);
}

/** The cron run: check due ideas; a freshly done one gets its follow-up drafts. */
export async function sweep(budgetMs = 100_000) {
  const app = githubApp();
  if (!app) return { configured: false, checked: 0, done: 0, drafted: 0, errors: [] as string[] };
  const t0 = Date.now();
  const { data, error } = await admin().from("ideas").select(WATCH_COLUMNS)
    .not("github_issue_number", "is", null).is("result_drafted_at", null)
    .order("github_checked_at", { ascending: true, nullsFirst: true }).limit(SWEEP_LIMIT * 3);
  if (error) throw error;
  const queue = ((data ?? []) as unknown as WatchedIdea[]).filter((i) => due(i)).slice(0, SWEEP_LIMIT);
  let checked = 0, done = 0, drafted = 0;
  const errors: string[] = [];
  for (const idea of queue) {
    if (Date.now() - t0 > budgetMs) break;
    try {
      const r = await checkIdea(idea, app);
      if (!r) {
        // The app can't reach the repo now: to the back of the queue.
        await admin().from("ideas").update({ github_checked_at: new Date().toISOString() }).eq("id", idea.id);
        continue;
      }
      checked++;
      if (r.outcome !== "done") continue;
      done++;
      const recent = !r.result.closed_at || Date.now() - Date.parse(r.result.closed_at) < AUTO_DRAFT_WINDOW_MS;
      const hasResult = !!r.idea.result_note?.trim() || !!(r.idea.result_links ?? []).length;
      if (recent && hasResult) {
        const { followups } = await shareResult(idea.id, {});
        drafted += followups.filter((f) => f.draft_id).length;
      }
    } catch (e) {
      errors.push(`${idea.id}: ${(e as Error).message.slice(0, 160)}`);
      await admin().from("ideas").update({ github_checked_at: new Date().toISOString() }).eq("id", idea.id);
    }
  }
  return { configured: true, checked, done, drafted, errors };
}
