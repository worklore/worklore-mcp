// Reading a GitHub Projects (v2) board and what happened to an idea's issue.
// Read-only: Hearback never moves a card or edits a board. Boards exist only
// in GraphQL, and an installation token reads them only on organizations
// whose installation granted "Organization projects: read".
// docs/ARCHITECTURE.md › GitHub App. Pure parts tested in github_boards_test.ts.

import { neutralize, titleWords, wordOverlap } from "./issues.ts";

// ------------------------------------------------------------------ boards

export interface BoardRef { owner: string; number: number }

export interface Board { id: string; owner: string; number: number; title: string; url: string; closed: boolean }

export const boardUrl = (owner: string, number: number) =>
  `https://github.com/orgs/${encodeURIComponent(owner)}/projects/${number}`;

/**
 * Pure. A board link or "owner/number" → its address. `user` for a board on a
 * personal account (github.com/users/…), which an app installation can't read.
 */
export function parseBoardRef(s: string): (BoardRef & { user: boolean }) | null {
  const t = s.trim();
  const url = t.match(/^(?:https?:\/\/)?(?:www\.)?github\.com\/(orgs|users)\/([A-Za-z0-9-]+)\/projects\/(\d+)(?:[/?#].*)?$/i);
  if (url) return { owner: url[2], number: Number(url[3]), user: url[1].toLowerCase() === "users" };
  const short = t.match(/^([A-Za-z0-9-]+)\/(\d+)$/);
  return short ? { owner: short[1], number: Number(short[2]), user: false } : null;
}

export const ORG_BOARDS = `query($login: String!) {
  organization(login: $login) {
    projectsV2(first: 50, orderBy: {field: UPDATED_AT, direction: DESC}) { nodes { id number title url closed } }
  }
}`;

export const ORG_BOARD = `query($login: String!, $number: Int!) {
  organization(login: $login) { projectV2(number: $number) { id number title url closed } }
}`;

type RawBoard = { id?: string; number?: number; title?: string; url?: string; closed?: boolean } | null;

const toBoard = (owner: string, b: RawBoard): Board | null =>
  b?.id && typeof b.number === "number"
    ? { id: b.id, owner, number: b.number, title: b.title ?? `Project ${b.number}`, url: b.url ?? boardUrl(owner, b.number), closed: !!b.closed }
    : null;

/** Pure. ORG_BOARDS data → the org's boards (open ones first). */
export function parseBoards(owner: string, data: unknown): Board[] {
  const nodes = (data as { organization?: { projectsV2?: { nodes?: RawBoard[] } } | null })?.organization?.projectsV2?.nodes ?? [];
  return nodes.map((n) => toBoard(owner, n)).filter((b): b is Board => !!b)
    .sort((a, b) => Number(a.closed) - Number(b.closed));
}

/** Pure. ORG_BOARD data → the board, or null. */
export function parseBoard(owner: string, data: unknown): Board | null {
  return toBoard(owner, (data as { organization?: { projectV2?: RawBoard } | null })?.organization?.projectV2 ?? null);
}

// ------------------------------------------------------------------ board items (duplicate check)

/** Pages of 100; the duplicate check reads at most this many items. */
export const MAX_BOARD_PAGES = 5;

export const BOARD_ITEMS = `query($id: ID!, $after: String) {
  node(id: $id) {
    ... on ProjectV2 {
      items(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isArchived
          status: fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
          content {
            __typename
            ... on Issue { number title url state repository { nameWithOwner } }
            ... on PullRequest { number title url state repository { nameWithOwner } }
            ... on DraftIssue { title }
          }
        }
      }
    }
  }
}`;

export interface BoardItem {
  type: "issue" | "pr" | "draft";
  title: string;
  /** Null for a draft (it lives only on the board). */
  url: string | null;
  number: number | null;
  repo: string | null;
  /** open / closed / merged (GitHub's, lower case); null for a draft. */
  state: string | null;
  /** The board's Status column ("Todo", "In progress", "Done"). */
  status: string | null;
}

/** Pure. One BOARD_ITEMS page → its items (archived and redacted ones dropped) and the next cursor. */
export function parseBoardItems(data: unknown): { items: BoardItem[]; next: string | null } {
  const items = (data as { node?: { items?: { pageInfo?: { hasNextPage?: boolean; endCursor?: string | null }; nodes?: unknown[] } } | null })?.node?.items;
  const out: BoardItem[] = [];
  for (const raw of items?.nodes ?? []) {
    const n = raw as {
      isArchived?: boolean; status?: { name?: string } | null;
      content?: { __typename?: string; number?: number; title?: string; url?: string; state?: string; repository?: { nameWithOwner?: string } } | null;
    };
    const c = n.content;
    if (n.isArchived || !c?.title) continue;
    const type = c.__typename === "Issue" ? "issue" : c.__typename === "PullRequest" ? "pr" : c.__typename === "DraftIssue" ? "draft" : null;
    if (!type) continue;
    out.push({
      type, title: c.title, url: c.url ?? null, number: c.number ?? null, repo: c.repository?.nameWithOwner ?? null,
      state: c.state ? c.state.toLowerCase() : null, status: n.status?.name?.trim() || null,
    });
  }
  const next = items?.pageInfo?.hasNextPage ? items.pageInfo.endCursor ?? null : null;
  return { items: out, next };
}

export interface BoardMatch extends BoardItem { score: number }

/**
 * Pure. Board items that read like the same ask, best first, ≤ 3. Pull
 * requests are left out (a PR is work, not an ask); `skipUrls` are already
 * shown as repo look-alikes.
 */
export function boardMatches(items: BoardItem[], title: string, skipUrls: string[] = [], minScore = 0.25): BoardMatch[] {
  const want = new Set(titleWords(title));
  if (!want.size) return [];
  const skip = new Set(skipUrls.map((u) => u.toLowerCase()));
  return items
    .filter((i) => i.type !== "pr" && !(i.url && skip.has(i.url.toLowerCase())))
    .map((i) => ({ ...i, score: wordOverlap(want, i.title) }))
    .filter((i) => i.score >= minScore)
    // Equally alike: a finished one first (then there's a result to share, not an issue to open).
    .sort((a, b) => b.score - a.score || Number(isDoneStatus(b.status)) - Number(isDoneStatus(a.status)))
    .slice(0, 3);
}

/** Pure. A Status option that means the work is finished ("Done", "✅ Shipped", "Released"). */
export function isDoneStatus(name: string | null | undefined): boolean {
  const w = (name ?? "").toLowerCase().replace(/[^a-z ]+/g, " ").trim();
  return /^(done|shipped|released|complete|completed|live|published|finished)$/.test(w);
}

// ------------------------------------------------------------------ issue result

export const ISSUE_RESULT = `query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      state stateReason closedAt url
      closedByPullRequestsReferences(first: 5, includeClosedPrs: true) { nodes { number title url merged } }
      timelineItems(last: 3, itemTypes: [CLOSED_EVENT]) {
        nodes { ... on ClosedEvent { closer { __typename ... on PullRequest { number title url merged } ... on Commit { abbreviatedOid messageHeadline url } } } }
      }
      comments(last: 10) { nodes { body url createdAt authorAssociation author { __typename login } } }
      projectItems(first: 10) {
        nodes { project { id } status: fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } } }
      }
    }
  }
}`;

export interface ResultLink { title: string; url: string; kind: "pr" | "commit" | "link" }

export interface IssueResult {
  state: "open" | "closed";
  /** completed / not_planned / duplicate / reopened, or null. */
  reason: string | null;
  closed_at: string | null;
  /** The Status on the linked board, if the issue is there and the app may read it. */
  board_status: string | null;
  /** The last maintainer comment (what was done), cleaned; null if none. */
  note: string | null;
  note_url: string | null;
  links: ResultLink[];
}

/** Only the people who run the repo speak for the result. */
const MAINTAINERS = new Set(["OWNER", "MEMBER", "COLLABORATOR"]);
const HEARBACK_FOOTER = /\]\(https:\/\/hearback\.dev\)/;
export const MAX_NOTE = 1500;
const MAX_LINKS = 6;

/** Pure. A comment body → the words worth retelling: no quotes, HTML comments, task boxes or images. */
export function cleanNote(body: string): string {
  return body.replace(/\r\n/g, "\n")
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .split("\n").filter((l) => !/^\s*>/.test(l)).join("\n")
    .replace(/^[ \t]*[-*] \[[ xX]\][ \t]*/gm, "- ")
    .replace(/\n{3,}/g, "\n\n").trim();
}

/** Pure. Markdown links first ([title](url)), then bare URLs, in order, deduplicated. */
export function linksIn(text: string): ResultLink[] {
  const out: ResultLink[] = [];
  const seen = new Set<string>();
  const add = (title: string, url: string) => {
    const u = url.replace(/[.,;:!?)]+$/, "");
    if (seen.has(u.toLowerCase())) return;
    seen.add(u.toLowerCase());
    out.push({ title: title.trim() || u, url: u, kind: "link" });
  };
  for (const m of text.matchAll(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g)) add(m[1], m[2]);
  const bare = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, " ");
  for (const m of bare.matchAll(/https?:\/\/[^\s<>()"']+/g)) add("", m[0]);
  return out;
}

/**
 * Pure. ISSUE_RESULT data → what happened. `boardId` picks the Status from
 * the project's linked board (else the first board that has one).
 */
export function readIssueResult(data: unknown, boardId: string | null): IssueResult | null {
  type PR = { __typename?: string; number?: number; title?: string; url?: string; merged?: boolean; abbreviatedOid?: string; messageHeadline?: string };
  const issue = (data as { repository?: { issue?: {
    state?: string; stateReason?: string | null; closedAt?: string | null; url?: string;
    closedByPullRequestsReferences?: { nodes?: (PR | null)[] } | null;
    timelineItems?: { nodes?: ({ closer?: PR | null } | null)[] } | null;
    comments?: { nodes?: ({ body?: string; url?: string; createdAt?: string; authorAssociation?: string; author?: { __typename?: string; login?: string } | null } | null)[] } | null;
    projectItems?: { nodes?: ({ project?: { id?: string } | null; status?: { name?: string } | null } | null)[] } | null;
  } | null } | null })?.repository?.issue;
  if (!issue?.state) return null;

  const items = (issue.projectItems?.nodes ?? []).filter(Boolean) as { project?: { id?: string } | null; status?: { name?: string } | null }[];
  const onBoard = (boardId ? items.find((i) => i.project?.id === boardId) : null) ?? items.find((i) => i.status?.name);
  const board_status = onBoard?.status?.name?.trim() || null;

  const links: ResultLink[] = [];
  const seen = new Set<string>();
  const push = (l: ResultLink) => {
    if (!l.url || seen.has(l.url.toLowerCase()) || links.length >= MAX_LINKS) return;
    if (issue.url && l.url.toLowerCase().startsWith(issue.url.toLowerCase())) return; // the issue itself
    seen.add(l.url.toLowerCase());
    links.push(l);
  };
  const pr = (p: PR | null | undefined) => {
    if (!p?.url) return;
    if (p.__typename === "Commit") push({ title: p.messageHeadline || `Commit ${p.abbreviatedOid ?? ""}`.trim(), url: p.url, kind: "commit" });
    else if (p.merged !== false) push({ title: `#${p.number} ${p.title ?? ""}`.trim(), url: p.url, kind: "pr" });
  };
  for (const n of issue.timelineItems?.nodes ?? []) pr(n?.closer);
  for (const p of issue.closedByPullRequestsReferences?.nodes ?? []) pr(p ? { ...p, __typename: "PullRequest" } : null);

  const said = (issue.comments?.nodes ?? []).filter((c): c is NonNullable<typeof c> =>
    !!c?.body && MAINTAINERS.has(c.authorAssociation ?? "") && c.author?.__typename !== "Bot" && !HEARBACK_FOOTER.test(c.body));
  const last = said.at(-1);
  let note: string | null = null;
  if (last) {
    const clean = cleanNote(last.body!);
    if (clean) {
      note = clean.length > MAX_NOTE ? clean.slice(0, MAX_NOTE).replace(/\s+\S*$/, "") + " …" : clean;
      for (const l of linksIn(clean)) push(l);
    }
  }
  return {
    state: issue.state.toLowerCase() === "closed" ? "closed" : "open",
    reason: issue.stateReason ? issue.stateReason.toLowerCase() : null,
    closed_at: issue.closedAt ?? null,
    board_status, note, note_url: last?.url ?? null, links,
  };
}

/**
 * Pure. done: closed as completed (or the board says Done); dropped: closed
 * as not planned or a duplicate; open: still being worked on.
 */
export function outcome(r: Pick<IssueResult, "state" | "reason" | "board_status">): "done" | "dropped" | "open" {
  if (r.state === "closed" && (r.reason === "not_planned" || r.reason === "duplicate")) return isDoneStatus(r.board_status) ? "done" : "dropped";
  if (r.state === "closed" || isDoneStatus(r.board_status)) return "done";
  return "open";
}

/**
 * Pure. The result as the draft's note sees it: what was done and where to
 * read more. Other people's @mentions are neutralized (the reply may quote it).
 */
export function resultForDraft(r: { note: string | null; links: ResultLink[] }, issueTitle: string): string {
  const parts = [`What was asked: ${neutralize(issueTitle)}`];
  if (r.note?.trim()) parts.push(`What was done (her team's words on the issue):\n${neutralize(r.note.trim())}`);
  if (r.links.length) parts.push(`Links to point to (pick the one that shows it best):\n${r.links.map((l) => `- ${neutralize(l.title)}: ${l.url}`).join("\n")}`);
  return parts.join("\n\n");
}
