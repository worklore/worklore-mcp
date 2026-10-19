// POST /functions/v1/github   {action, ...}   (signed-in founder; docs/API.md › github)
//   status        {project_id, refresh?}        installations linked to the project, their repos, the linked repo's access
//   install_url   {project_id, client?}         one-time https://github.com/apps/hearback-dev/installations/new?state=…
//   link_repo     {project_id, repo|null}       owners: set projects.github_repo to a repo an installation can reach
//   idea_from_item {item_id}                   any comment → an idea (joins a matching one), so it can become an issue
//   issue_preview {idea_id}                     title, body (people's words), labels that exist, open look-alike issues
//   create_issue  {idea_id, title?, body?, labels?}  opens the issue (only on her tap), stores it on the idea, a touch per person
//   comment_issue {idea_id, number, body?}      adds the asks to an existing issue instead
//   boards        {project_id}                  the linked organizations' boards (Projects v2), or why not
//   link_board    {project_id, owner, number} | {project_id, board: null}   owners: the board to read (never written)
//   issue_result  {idea_id, refresh?}           what happened to the idea's issue (refresh: read GitHub now)
//   share_result  {idea_id, note?, links?}      her words for the result; a follow-up draft per person who asked
// Installation tokens are minted per request from the app key (cached ≤ 50 min).

import "../_shared/connectors/mod.ts";
import { APP_SLUG, githubApp, GithubApiError, GithubApp, GithubGraphqlError, installUrl, isForbidden } from "../_shared/connectors/github/app.ts";
import { BoardMatch, boardMatches, boardUrl, ORG_BOARD, parseBoard, parseBoardRef, ResultLink } from "../_shared/connectors/github/boards.ts";
import { duplicateQueries, issueBody, issueComment, IssueAsk, issueNumberFromUrl, parseDuplicates, pickLabels } from "../_shared/connectors/github/issues.ts";
import { newStateToken, STATE_TTL_MS } from "../_shared/connectors/github/install.ts";
import { fileFeedback } from "../_shared/core/ideas.ts";
import { admin, Caller, requireMember, requireUser } from "../_shared/server/ctx.ts";
import { installationForRepo, orgInstallation, projectBoards, projectInstallations, readBoardItems, syncProjectInstallations } from "../_shared/server/github.ts";
import { checkIdea, shareResult, WATCH_COLUMNS, WatchedIdea } from "../_shared/server/github_results.ts";
import { bad, HttpError, serve, str, uuid } from "../_shared/server/http.ts";
import { decider } from "../_shared/server/models.ts";
import { firstSentence } from "../_shared/server/text.ts";
import { tagUsage } from "../_shared/server/usage.ts";

type User = Extract<Caller, { kind: "user" }>;
const REPO_RE = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;

function requireApp(): GithubApp {
  const app = githubApp();
  if (!app) throw new HttpError(503, "github_not_configured", "GitHub isn't set up on the server yet.");
  return app;
}

function upstream(e: unknown): never {
  if (e instanceof GithubApiError) {
    if (e.rateLimited) throw new HttpError(429, "rate_limited", "GitHub's rate limit was reached. Try again in a few minutes.", { reset_at: e.resetAt });
    if (e.status === 403 || e.status === 404) {
      throw new HttpError(422, "github_no_access", "Hearback.dev can't reach that repo. Check which repositories the app may access on GitHub.", { status: e.status });
    }
    if (e.status === 410) throw new HttpError(422, "issues_disabled", "Issues are turned off in that repo.");
    if (e.status === 422) throw new HttpError(422, "github_rejected", "GitHub rejected the issue.", { github: e.body.slice(0, 300) });
    throw new HttpError(502, "upstream_error", "GitHub didn't answer. Try again.", { status: e.status });
  }
  throw e;
}

async function project(projectId: string) {
  const { data, error } = await admin().from("projects")
    .select("id, name, github_repo, github_board_owner, github_board_number, github_board_id, github_board_title").eq("id", projectId).maybeSingle();
  if (error) throw error;
  if (!data) throw new HttpError(404, "not_found", "No such project.");
  return data as {
    id: string; name: string; github_repo: string | null;
    github_board_owner: string | null; github_board_number: number | null; github_board_id: string | null; github_board_title: string | null;
  };
}

async function requireOwner(c: User, projectId: string) {
  const { data } = await admin().from("project_members").select("role").eq("project_id", projectId).eq("founder_id", c.userId).maybeSingle();
  if (!data) throw new HttpError(403, "forbidden", "You're not a member of this project.");
  if (data.role !== "owner") throw new HttpError(403, "forbidden", "Only the project's owner can change where ideas go.");
}

// ------------------------------------------------------------------ status / install / link

async function status(c: User, body: Record<string, unknown>) {
  const projectId = uuid(body.project_id, "project_id")!;
  await requireMember(c, projectId);
  const p = await project(projectId);
  const app = githubApp();
  // What GitHub grants now: an uninstalled app's repos are gone, stale lists are re-read.
  if (app) await syncProjectInstallations(projectId, app, body.refresh === true);
  const installs = await projectInstallations(projectId);
  const reach = p.github_repo && app ? await installationForRepo(projectId, p.github_repo, app) : null;
  return {
    configured: !!app,
    app_slug: APP_SLUG,
    repo: p.github_repo,
    // installation = issues through the API (private repos too); url = the pre-filled github.com page.
    repo_access: !p.github_repo ? null : reach ? "installation" : "url",
    repo_installation_id: reach?.installation.installation_id ?? null,
    board: boardOf(p),
    installations: installs.map((i) => ({
      installation_id: i.installation_id, account_login: i.account_login, account_type: i.account_type,
      repository_selection: i.repository_selection, suspended: !!i.suspended_at, manage_url: i.manage_url,
      repos_fetched_at: i.repos_fetched_at,
      repos: [...(i.repos ?? [])].filter((r) => !r.archived)
        .sort((a, b) => (b.pushed_at ?? "").localeCompare(a.pushed_at ?? "")),
    })),
  };
}

async function makeInstallUrl(c: User, body: Record<string, unknown>) {
  const projectId = uuid(body.project_id, "project_id")!;
  await requireMember(c, projectId);
  requireApp();
  const client = (str(body.client, "client", { max: 10 }) ?? "app");
  if (client !== "app" && client !== "web") throw bad("client must be app or web");
  const { token, hash } = await newStateToken();
  const expires = new Date(Date.now() + STATE_TTL_MS).toISOString();
  const { error } = await admin().from("github_install_states").insert({
    token_sha256: hash, founder_id: c.userId, project_id: projectId, client, expires_at: expires,
  });
  if (error) throw error;
  return { url: installUrl(token), expires_at: expires };
}

async function linkRepo(c: User, body: Record<string, unknown>) {
  const projectId = uuid(body.project_id, "project_id")!;
  await requireOwner(c, projectId);
  const raw = body.repo === null ? null : str(body.repo, "repo", { required: true, max: 140 })!.trim();
  if (raw !== null && !REPO_RE.test(raw)) throw bad("repo must be owner/name");
  let repo = raw;
  if (raw) {
    const reach = await installationForRepo(projectId, raw, requireApp());
    if (!reach) {
      throw new HttpError(422, "github_no_access", `Hearback.dev can't reach ${raw}. Add it to the app's repositories on GitHub, or connect GitHub for its owner.`);
    }
    repo = reach.repo.full_name; // GitHub's spelling
  }
  const { data, error } = await admin().from("projects").update({ github_repo: repo }).eq("id", projectId).select("*").single();
  if (error) throw error;
  return { project: data };
}

// ------------------------------------------------------------------ board (read-only)

function boardOf(p: Awaited<ReturnType<typeof project>>) {
  if (!p.github_board_owner || !p.github_board_number) return null;
  return {
    owner: p.github_board_owner, number: p.github_board_number, id: p.github_board_id,
    title: p.github_board_title ?? `Project ${p.github_board_number}`, url: boardUrl(p.github_board_owner, p.github_board_number),
  };
}

async function boards(c: User, body: Record<string, unknown>) {
  const projectId = uuid(body.project_id, "project_id")!;
  await requireMember(c, projectId);
  const p = await project(projectId);
  const { orgs, personal } = await projectBoards(projectId, requireApp());
  return { board: boardOf(p), orgs, personal };
}

async function linkBoard(c: User, body: Record<string, unknown>) {
  const projectId = uuid(body.project_id, "project_id")!;
  await requireOwner(c, projectId);
  const db = admin();
  if (body.board === null) {
    const { data, error } = await db.from("projects").update({
      github_board_owner: null, github_board_number: null, github_board_id: null, github_board_title: null,
    }).eq("id", projectId).select("*").single();
    if (error) throw error;
    return { project: data };
  }
  // owner + number, or a pasted link (github.com/orgs/<owner>/projects/<n>/views/…).
  const ref = typeof body.url === "string"
    ? parseBoardRef(str(body.url, "url", { max: 300 })!)
    : { owner: str(body.owner, "owner", { required: true, max: 40 })!, number: Number(body.number), user: false };
  if (!ref || !/^[A-Za-z0-9-]+$/.test(ref.owner) || !Number.isInteger(ref.number) || ref.number <= 0) {
    throw bad("give owner and number, or a github.com/orgs/<owner>/projects/<number> link");
  }
  if (ref.user) {
    throw new HttpError(422, "board_personal", "GitHub doesn't let apps read boards on a personal account. Use a board that belongs to an organization.");
  }
  const app = requireApp();
  const inst = await orgInstallation(projectId, ref.owner);
  if (!inst) {
    throw new HttpError(422, "github_not_installed", `Hearback.dev isn't installed on ${ref.owner}. Connect GitHub and pick the ${ref.owner} organization.`, { owner: ref.owner });
  }
  let board;
  try {
    const { data, errors } = await app.graphql(inst.installation_id, ORG_BOARD, { login: inst.account_login, number: ref.number });
    board = parseBoard(inst.account_login, data);
    if (!board && errors.some(isForbidden)) throw new GithubGraphqlError(errors);
  } catch (e) {
    if (e instanceof GithubGraphqlError && e.forbidden) throw noBoardPermission(inst);
    if (!(e instanceof GithubGraphqlError && e.notFound)) upstream(e);
  }
  if (!board) throw new HttpError(404, "board_not_found", `${ref.owner} has no board number ${ref.number} that Hearback.dev can see.`);
  const { data, error } = await db.from("projects").update({
    github_board_owner: board.owner, github_board_number: board.number, github_board_id: board.id, github_board_title: board.title,
  }).eq("id", projectId).select("*").single();
  if (error) throw error;
  return { project: data, board: { ...board } };
}

function noBoardPermission(inst: { account_login: string; manage_url: string }) {
  return new HttpError(422, "board_no_permission",
    `Hearback.dev may not read ${inst.account_login}'s boards yet. Accept the new "Projects: read" permission in the app's settings on GitHub.`,
    { manage_url: inst.manage_url });
}

/** Board items that read like this idea (any repo, drafts too), skipping repo look-alikes already shown. */
async function boardLookAlikes(app: GithubApp, projectId: string, title: string, skip: string[]): Promise<BoardMatch[]> {
  const p = await project(projectId);
  if (!p.github_board_id || !p.github_board_owner) return [];
  const inst = await orgInstallation(projectId, p.github_board_owner);
  if (!inst) return [];
  try {
    return boardMatches(await readBoardItems(app, inst.installation_id, p.github_board_id), title, skip);
  } catch (e) {
    // The repo check still stands without the board.
    console.error("github: board items:", (e as Error).message.slice(0, 160));
    return [];
  }
}

// ------------------------------------------------------------------ ideas → issues

interface IdeaRow {
  id: string; project_id: string; title: string; summary: string | null; kind: string; status: string;
  github_issue_url: string | null; github_issue_number: number | null; github_issue_repo: string | null;
}

async function loadIdea(c: User, ideaId: string) {
  // Through her own client: RLS decides whether she may see it.
  const { data: idea } = await c.db.from("ideas")
    .select("id, project_id, title, summary, kind, status, github_issue_url, github_issue_number, github_issue_repo")
    .eq("id", ideaId).maybeSingle();
  if (!idea) throw new HttpError(404, "not_found", "No such idea.");
  const db = admin();
  const { data: links } = await db.from("idea_items")
    .select("item_id, quote, created_at, items(text, url, platform, posted_at, person_id, people(display_name))")
    .eq("idea_id", ideaId).order("created_at", { ascending: true });
  const rows = (links ?? []) as unknown as {
    item_id: string; quote: string | null;
    items: {
      text: string; url: string | null; platform: string; posted_at: string | null; person_id: string;
      people: { display_name: string | null } | null;
    } | null;
  }[];
  const asks: (IssueAsk & { person_id: string })[] = rows.filter((r) => r.items).map((r) => ({
    person_id: r.items!.person_id,
    name: r.items!.people?.display_name?.trim() || "Someone",
    text: r.items!.text || r.quote || "",
    url: r.items!.url, platform: r.items!.platform, posted_at: r.items!.posted_at,
  }));
  const itemIds = rows.map((r) => r.item_id);
  const { data: th } = itemIds.length
    ? await db.from("item_themes").select("themes(name)").in("item_id", itemIds)
    : { data: [] };
  const themes = [...new Set(((th ?? []) as unknown as { themes: { name: string } | null }[]).map((t) => t.themes?.name).filter(Boolean) as string[])];
  return { idea: idea as IdeaRow, asks, themes };
}

/** "Make it a GitHub issue" on a comment triage didn't file as an idea: files it now (it joins a matching idea). */
async function ideaFromItem(c: User, body: Record<string, unknown>) {
  const itemId = uuid(body.item_id, "item_id")!;
  // Through her own client: RLS decides whether she may see it.
  const { data: item } = await c.db.from("items").select("id, project_id, person_id, text, triage_summary").eq("id", itemId).maybeSingle();
  if (!item) throw new HttpError(404, "not_found", "No such item.");
  tagUsage({ project_id: item.project_id, founder_id: c.userId, item_id: item.id });
  const summary = (item.triage_summary as string | null)?.trim() || firstSentence(item.text ?? "", 200);
  const ideaId = await fileFeedback(decider(), { ...item, text: item.text ?? "", summary });
  const { data, error } = await admin().from("ideas").select("*").eq("id", ideaId).single();
  if (error) throw error;
  return { idea: data };
}

async function repoFor(projectId: string) {
  const p = await project(projectId);
  if (!p.github_repo) throw new HttpError(422, "no_repo", "Link a GitHub repo in Project first.");
  const reach = await installationForRepo(projectId, p.github_repo, requireApp());
  if (!reach) {
    throw new HttpError(422, "github_not_installed", `Hearback.dev isn't installed on ${p.github_repo}. Connect GitHub in Project, or open the issue on github.com.`, { repo: p.github_repo });
  }
  return { repo: reach.repo.full_name, installationId: reach.installation.installation_id, hasIssues: reach.repo.has_issues };
}

async function duplicates(app: GithubApp, installationId: number, repo: string, title: string) {
  for (const q of duplicateQueries(repo, title)) {
    const json = await app.asInstallation<unknown>(installationId, "GET", `/search/issues?q=${encodeURIComponent(q)}&per_page=10`);
    const found = parseDuplicates(json, title);
    if (found.length) return found;
  }
  return [];
}

async function repoLabels(app: GithubApp, installationId: number, repo: string): Promise<string[]> {
  const labels = await app.asInstallation<{ name: string }[]>(installationId, "GET", `/repos/${repo}/labels?per_page=100`);
  return (labels ?? []).map((l) => l.name);
}

async function preview(c: User, body: Record<string, unknown>) {
  const { idea, asks, themes } = await loadIdea(c, uuid(body.idea_id, "idea_id")!);
  const app = requireApp();
  const { repo, installationId, hasIssues } = await repoFor(idea.project_id);
  if (!hasIssues) throw new HttpError(422, "issues_disabled", `Issues are turned off in ${repo}.`);
  try {
    const [dups, existing] = await Promise.all([
      duplicates(app, installationId, repo, idea.title),
      repoLabels(app, installationId, repo),
    ]);
    const onBoard = await boardLookAlikes(app, idea.project_id, idea.title, dups.map((d) => d.url));
    return {
      repo, title: idea.title.slice(0, 256),
      body: issueBody({ title: idea.title, summary: idea.summary, kind: idea.kind, themes }, asks),
      comment: issueComment(asks),
      labels: pickLabels(existing, idea.kind),
      duplicates: dups,
      // The linked board's items that read alike (other repos, drafts, done ones: with their Status).
      board_matches: onBoard,
      people: new Set(asks.map((a) => a.person_id)).size,
      // A pre-filled github.com "new issue" link (the fallback) is not an issue yet.
      existing_issue: issueNumberFromUrl(idea.github_issue_url) ? { url: idea.github_issue_url, number: issueNumberFromUrl(idea.github_issue_url) } : null,
    };
  } catch (e) {
    upstream(e);
  }
}

/** The idea now points at the issue; each person who asked gets a touch. */
async function recordIssue(c: User, idea: IdeaRow, asks: (IssueAsk & { person_id: string })[], issue: { number: number; html_url: string }, repo: string, how: "created" | "commented") {
  const db = admin();
  const { data: updated, error } = await db.from("ideas").update({
    status: "issue_open", github_issue_url: issue.html_url, github_issue_number: issue.number, github_issue_repo: repo,
    // Not read yet (it may be a done issue she linked to): the next sweep reads it first.
    github_issue_state: null, github_issue_state_reason: null, github_issue_closed_at: null, github_board_status: null,
    github_checked_at: null, result_drafted_at: null,
    updated_at: new Date().toISOString(),
  }).eq("id", idea.id).select("*").single();
  if (error) throw error;
  const now = new Date().toISOString();
  const people = [...new Set(asks.map((a) => a.person_id))];
  if (people.length) {
    const text = how === "created" ? `Turned into issue #${issue.number}: ${idea.title}`.slice(0, 300) : `Added to issue #${issue.number}: ${idea.title}`.slice(0, 300);
    const { error: tErr } = await db.from("touches").insert(people.map((person_id) => ({
      project_id: idea.project_id, person_id, direction: "out", platform: "github", kind: "issue",
      occurred_at: now, url: issue.html_url, text, by_founder: c.userId, source: "hearback",
      meta: { idea_id: idea.id, repo, issue_number: issue.number, how },
    })));
    if (tErr) console.error("github: touches failed:", tErr.message);
  }
  return updated;
}

async function createIssue(c: User, body: Record<string, unknown>) {
  const { idea, asks, themes } = await loadIdea(c, uuid(body.idea_id, "idea_id")!);
  if (issueNumberFromUrl(idea.github_issue_url)) throw new HttpError(409, "already_has_issue", "This idea already has an issue.", { url: idea.github_issue_url });
  const app = requireApp();
  const { repo, installationId } = await repoFor(idea.project_id);
  const title = (str(body.title, "title", { max: 256 }) ?? idea.title).trim().slice(0, 256);
  if (!title) throw bad("title is empty");
  const text = str(body.body, "body", { max: 60_000 }) ??
    issueBody({ title: idea.title, summary: idea.summary, kind: idea.kind, themes }, asks);
  let labels: string[] = [];
  try {
    const existing = await repoLabels(app, installationId, repo);
    const wanted = Array.isArray(body.labels) ? (body.labels as unknown[]).filter((l): l is string => typeof l === "string") : pickLabels(existing, idea.kind);
    // Never creates a label: only the ones the repo has (GitHub would create unknown ones).
    const have = new Map(existing.map((l) => [l.toLowerCase(), l]));
    labels = [...new Set(wanted.map((w) => have.get(w.toLowerCase())).filter(Boolean) as string[])].slice(0, 5);
    const issue = await app.asInstallation<{ number: number; html_url: string }>(installationId, "POST", `/repos/${repo}/issues`,
      { title, body: text, ...(labels.length ? { labels } : {}) });
    const updated = await recordIssue(c, idea, asks, issue, repo, "created");
    return { issue: { number: issue.number, url: issue.html_url, repo, labels }, idea: updated };
  } catch (e) {
    upstream(e);
  }
}

async function commentIssue(c: User, body: Record<string, unknown>) {
  const { idea, asks } = await loadIdea(c, uuid(body.idea_id, "idea_id")!);
  const number = Number(body.number);
  if (!Number.isInteger(number) || number <= 0) throw bad("number must be an issue number");
  const app = requireApp();
  const { repo, installationId } = await repoFor(idea.project_id);
  const text = str(body.body, "body", { max: 60_000 }) ?? issueComment(asks);
  try {
    const issue = await app.asInstallation<{ number: number; html_url: string; state: string; pull_request?: unknown }>(
      installationId, "GET", `/repos/${repo}/issues/${number}`);
    if (issue.pull_request) throw new HttpError(422, "not_an_issue", `#${number} is a pull request.`);
    const comment = await app.asInstallation<{ html_url: string }>(installationId, "POST", `/repos/${repo}/issues/${number}/comments`, { body: text });
    const updated = await recordIssue(c, idea, asks, { number, html_url: issue.html_url }, repo, "commented");
    return { issue: { number, url: issue.html_url, repo, comment_url: comment.html_url }, idea: updated };
  } catch (e) {
    upstream(e);
  }
}

// ------------------------------------------------------------------ results → follow-ups

async function watchedIdea(c: User, ideaId: string): Promise<WatchedIdea> {
  // Through her own client: RLS decides whether she may see it.
  const { data } = await c.db.from("ideas").select(WATCH_COLUMNS).eq("id", ideaId).maybeSingle();
  if (!data) throw new HttpError(404, "not_found", "No such idea.");
  const idea = data as unknown as WatchedIdea;
  if (!idea.github_issue_number) throw new HttpError(422, "no_issue", "This idea has no GitHub issue yet.");
  return idea;
}

async function issueResult(c: User, body: Record<string, unknown>) {
  let idea = await watchedIdea(c, uuid(body.idea_id, "idea_id")!);
  if (body.refresh === true) {
    try {
      const r = await checkIdea(idea, requireApp());
      if (!r) throw new HttpError(422, "github_not_installed", `Hearback.dev can't reach ${idea.github_issue_repo}. Connect GitHub in Project.`);
      idea = r.idea;
    } catch (e) {
      if (e instanceof GithubGraphqlError) throw new HttpError(502, "upstream_error", "GitHub didn't answer. Try again.");
      upstream(e);
    }
  }
  const { data, error } = await admin().from("ideas").select("*").eq("id", idea.id).single();
  if (error) throw error;
  return { idea: data };
}

async function share(c: User, body: Record<string, unknown>) {
  const idea = await watchedIdea(c, uuid(body.idea_id, "idea_id")!);
  const note = body.note === undefined ? undefined : (str(body.note, "note", { max: 4000 }) ?? "").trim() || null;
  let links: ResultLink[] | undefined;
  if (body.links !== undefined) {
    if (!Array.isArray(body.links) || body.links.length > 8) throw bad("links must be a list of up to 8 {title, url}");
    links = body.links.map((l: unknown, i: number) => {
      const o = (l ?? {}) as Record<string, unknown>;
      const url = str(o.url, `links[${i}].url`, { required: true, max: 500 })!.trim();
      if (!/^https?:\/\/\S+$/.test(url)) throw bad(`links[${i}].url must be a web link`);
      const kind = o.kind === "pr" || o.kind === "commit" ? o.kind : "link";
      return { title: (str(o.title, `links[${i}].title`, { max: 200 }) ?? "").trim() || url, url, kind };
    });
  }
  if (note !== undefined || links !== undefined) {
    const { error } = await admin().from("ideas").update({
      ...(note !== undefined ? { result_note: note } : {}), ...(links !== undefined ? { result_links: links } : {}),
      updated_at: new Date().toISOString(),
    }).eq("id", idea.id);
    if (error) throw error;
  }
  const { followups } = await shareResult(idea.id, { founderId: c.userId, requestedBy: c.userId });
  const { data } = await admin().from("ideas").select("*").eq("id", idea.id).single();
  return { idea: data, followups, drafted: followups.filter((f) => f.draft_id).length };
}

serve(async (req, body) => {
  const c = await requireUser(req);
  const action = str(body.action, "action", { required: true, max: 30 });
  switch (action) {
    case "status": return await status(c, body);
    case "install_url": return await makeInstallUrl(c, body);
    case "link_repo": return await linkRepo(c, body);
    case "idea_from_item": return await ideaFromItem(c, body);
    case "issue_preview": return await preview(c, body);
    case "create_issue": return await createIssue(c, body);
    case "comment_issue": return await commentIssue(c, body);
    case "boards": return await boards(c, body);
    case "link_board": return await linkBoard(c, body);
    case "issue_result": return await issueResult(c, body);
    case "share_result": return await share(c, body);
    default: throw bad("action must be status, install_url, link_repo, idea_from_item, issue_preview, create_issue, comment_issue, boards, link_board, issue_result or share_result");
  }
});
