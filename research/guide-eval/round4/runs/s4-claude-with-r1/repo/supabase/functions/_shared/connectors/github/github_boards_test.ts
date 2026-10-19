// GitHub boards and issue results: board links, board lists and items, the
// board look-alike check, Done statuses, reading what happened to an issue
// (closing PRs, the maintainer's note, its links, the board Status), the
// outcome, the draft's result text, and GraphQL through an installation.
//   deno test -A supabase/functions/_shared/

import { assert, assertEquals, assertRejects } from "jsr:@std/assert@1";
import { GithubApp, GithubGraphqlError, RawInstallation } from "./app.ts";
import {
  BoardItem, boardMatches, cleanNote, isDoneStatus, linksIn, MAX_NOTE, outcome, parseBoard, parseBoardItems, parseBoardRef, parseBoards,
  readIssueResult, resultForDraft,
} from "./boards.ts";
import { due, ideaStatusFor, mergeLinks } from "../../server/github_results.ts";
import { syncPlan } from "../../server/github.ts";
import { intentNote } from "../../core/draft_run.ts";

Deno.test("parseBoardRef: org links (any view), owner/number, personal boards flagged", () => {
  assertEquals(parseBoardRef("https://github.com/orgs/worklore/projects/2/views/2"), { owner: "worklore", number: 2, user: false });
  assertEquals(parseBoardRef("github.com/orgs/worklore/projects/12?pane=issue"), { owner: "worklore", number: 12, user: false });
  assertEquals(parseBoardRef("worklore/3"), { owner: "worklore", number: 3, user: false });
  assertEquals(parseBoardRef("https://github.com/users/ana/projects/1"), { owner: "ana", number: 1, user: true });
  assertEquals(parseBoardRef("https://github.com/worklore/hearback"), null);
  assertEquals(parseBoardRef("https://github.com/orgs/worklore/projects/x"), null);
});

Deno.test("parseBoards / parseBoard: open boards first; missing ones are null", () => {
  const data = { organization: { projectsV2: { nodes: [
    { id: "P1", number: 1, title: "Old", url: "https://github.com/orgs/w/projects/1", closed: true },
    { id: "P2", number: 2, title: "Roadmap", url: "https://github.com/orgs/w/projects/2", closed: false },
    null,
  ] } } };
  assertEquals(parseBoards("w", data).map((b) => [b.number, b.closed]), [[2, false], [1, true]]);
  assertEquals(parseBoards("w", { organization: null }), []);
  assertEquals(parseBoard("w", { organization: { projectV2: { id: "P2", number: 2, title: "Roadmap" } } })?.url, "https://github.com/orgs/w/projects/2");
  assertEquals(parseBoard("w", { organization: { projectV2: null } }), null);
});

const page = (nodes: unknown[], next: string | null = null) => ({
  node: { items: { pageInfo: { hasNextPage: !!next, endCursor: next }, nodes } },
});

Deno.test("parseBoardItems: issues, PRs and drafts with Status; archived and redacted ones dropped", () => {
  const r = parseBoardItems(page([
    { isArchived: false, status: { name: "In progress" }, content: { __typename: "Issue", number: 4, title: "Dark mode", url: "https://github.com/w/a/issues/4", state: "OPEN", repository: { nameWithOwner: "w/a" } } },
    { isArchived: false, status: null, content: { __typename: "DraftIssue", title: "Export to CSV" } },
    { isArchived: true, status: { name: "Done" }, content: { __typename: "Issue", number: 1, title: "Old", url: "u", state: "CLOSED" } },
    { isArchived: false, status: { name: "Done" }, content: null },
    { isArchived: false, status: { name: "Done" }, content: { __typename: "PullRequest", number: 9, title: "Dark mode PR", url: "https://github.com/w/a/pull/9", state: "MERGED", repository: { nameWithOwner: "w/a" } } },
  ], "CUR"));
  assertEquals(r.next, "CUR");
  assertEquals(r.items.map((i) => [i.type, i.title, i.status, i.state]), [
    ["issue", "Dark mode", "In progress", "open"],
    ["draft", "Export to CSV", null, null],
    ["pr", "Dark mode PR", "Done", "merged"],
  ]);
  assertEquals(parseBoardItems(page([])).next, null);
});

Deno.test("boardMatches: same-ask items from any repo and drafts; PRs and shown repo look-alikes skipped", () => {
  const items: BoardItem[] = [
    { type: "issue", title: "Export replies to CSV", url: "https://github.com/w/other/issues/3", number: 3, repo: "w/other", state: "closed", status: "Done" },
    { type: "draft", title: "CSV export of replies", url: null, number: null, repo: null, state: null, status: "Todo" },
    { type: "pr", title: "Export replies to CSV", url: "https://github.com/w/a/pull/8", number: 8, repo: "w/a", state: "merged", status: "Done" },
    { type: "issue", title: "Export replies CSV", url: "https://github.com/w/a/issues/5", number: 5, repo: "w/a", state: "open", status: null },
    { type: "issue", title: "Dark mode", url: "https://github.com/w/a/issues/6", number: 6, repo: "w/a", state: "open", status: null },
  ];
  const m = boardMatches(items, "Export replies as CSV", ["https://github.com/w/a/issues/5"]);
  assertEquals(m.map((i) => [i.type, i.number, i.status]), [["issue", 3, "Done"], ["draft", null, "Todo"]]);
  assert(m[0].score > 0.5);
  assertEquals(boardMatches(items, "the and"), [], "no searchable words");
});

Deno.test("isDoneStatus: Done-like options, with emoji and case; not In progress", () => {
  for (const s of ["Done", "✅ Done", "shipped", "Released", "Completed"]) assert(isDoneStatus(s), s);
  for (const s of ["In progress", "Todo", "Done-ish soon", "", null]) assert(!isDoneStatus(s), String(s));
});

const issueData = (over: Record<string, unknown> = {}) => ({ repository: { issue: {
  state: "CLOSED", stateReason: "COMPLETED", closedAt: "2026-10-12T10:00:00Z", url: "https://github.com/w/a/issues/12",
  closedByPullRequestsReferences: { nodes: [
    { number: 30, title: "Add CSV export", url: "https://github.com/w/a/pull/30", merged: true },
    { number: 29, title: "Abandoned try", url: "https://github.com/w/a/pull/29", merged: false },
  ] },
  timelineItems: { nodes: [{ closer: { __typename: "PullRequest", number: 30, title: "Add CSV export", url: "https://github.com/w/a/pull/30", merged: true } }] },
  comments: { nodes: [
    { body: "Me too!", url: "c1", createdAt: "2026-10-01T00:00:00Z", authorAssociation: "NONE", author: { __typename: "User", login: "x" } },
    { body: "More asked:\n\n> words\n\n---\n_Added from [Hearback](https://hearback.dev)._", url: "c2", createdAt: "2026-10-02T00:00:00Z", authorAssociation: "OWNER", author: { __typename: "Bot", login: "hearback-dev[bot]" } },
    { body: "Shipped in 1.4: Settings › Export. Write-up: [CSV export notes](https://worklore.dev/s/csv)\n<!-- hidden -->\n> quoted ask\n![shot](https://img/x.png)", url: "https://github.com/w/a/issues/12#c3", createdAt: "2026-10-12T09:59:00Z", authorAssociation: "MEMBER", author: { __typename: "User", login: "val" } },
    { body: "Thanks!", url: "c4", createdAt: "2026-10-12T11:00:00Z", authorAssociation: "CONTRIBUTOR", author: { __typename: "User", login: "y" } },
  ] },
  projectItems: { nodes: [
    { project: { id: "OTHER" }, status: { name: "Backlog" } },
    { project: { id: "BOARD" }, status: { name: "Done" } },
  ] },
  ...over,
} } });

Deno.test("readIssueResult: state, the maintainer's note (cleaned), merged closing PRs and the note's links, the linked board's Status", () => {
  const r = readIssueResult(issueData(), "BOARD")!;
  assertEquals([r.state, r.reason, r.closed_at, r.board_status], ["closed", "completed", "2026-10-12T10:00:00Z", "Done"]);
  assertEquals(r.note, "Shipped in 1.4: Settings › Export. Write-up: [CSV export notes](https://worklore.dev/s/csv)");
  assertEquals(r.note_url, "https://github.com/w/a/issues/12#c3");
  assertEquals(r.links.map((l) => [l.kind, l.url]), [
    ["pr", "https://github.com/w/a/pull/30"],
    ["link", "https://worklore.dev/s/csv"],
  ]);
  assertEquals(readIssueResult(issueData(), null)!.board_status, "Backlog", "no linked board: the first Status");
  // projectItems unreadable (no permission): null field, the rest still reads.
  assertEquals(readIssueResult(issueData({ projectItems: null }), "BOARD")!.board_status, null);
  assertEquals(readIssueResult({ repository: { issue: null } }, null), null);
  const open = readIssueResult(issueData({ state: "OPEN", stateReason: null, closedAt: null, comments: { nodes: [] }, closedByPullRequestsReferences: null, timelineItems: null }), null)!;
  assertEquals([open.state, open.note, open.links], ["open", null, []]);
});

Deno.test("readIssueResult: a commit closer; a long note is cut at a word", () => {
  const r = readIssueResult(issueData({
    closedByPullRequestsReferences: { nodes: [] },
    timelineItems: { nodes: [{ closer: { __typename: "Commit", abbreviatedOid: "abc123", messageHeadline: "Fix #12: export", url: "https://github.com/w/a/commit/abc123" } }] },
    comments: { nodes: [{ body: "word ".repeat(600), url: "c", createdAt: "x", authorAssociation: "OWNER", author: { __typename: "User", login: "v" } }] },
  }), null)!;
  assertEquals(r.links, [{ title: "Fix #12: export", url: "https://github.com/w/a/commit/abc123", kind: "commit" }]);
  assert(r.note!.length <= MAX_NOTE + 2 && r.note!.endsWith(" …"));
});

Deno.test("cleanNote / linksIn", () => {
  assertEquals(cleanNote("Done.\r\n\r\n\r\n- [x] tests\n> quote"), "Done.\n\n- tests");
  assertEquals(linksIn("See [the post](https://a.dev/p). Also https://b.dev/x, and https://a.dev/p again.").map((l) => [l.title, l.url]), [
    ["the post", "https://a.dev/p"], ["https://b.dev/x", "https://b.dev/x"],
  ]);
});

Deno.test("outcome: completed or board Done → done; not planned → dropped (unless the board says Done); else open", () => {
  assertEquals(outcome({ state: "closed", reason: "completed", board_status: null }), "done");
  assertEquals(outcome({ state: "closed", reason: null, board_status: null }), "done");
  assertEquals(outcome({ state: "open", reason: null, board_status: "Done" }), "done");
  assertEquals(outcome({ state: "closed", reason: "not_planned", board_status: "Backlog" }), "dropped");
  assertEquals(outcome({ state: "closed", reason: "duplicate", board_status: null }), "dropped");
  assertEquals(outcome({ state: "open", reason: "reopened", board_status: "In progress" }), "open");
});

Deno.test("ideaStatusFor / due / mergeLinks", () => {
  assertEquals(ideaStatusFor("issue_open", "done"), "done");
  assertEquals(ideaStatusFor("issue_open", "dropped"), "not_now");
  assertEquals(ideaStatusFor("done", "open"), "issue_open", "reopened");
  assertEquals(ideaStatusFor("not_now", "open"), "not_now", "her own Not now stays");
  const now = Date.parse("2026-10-14T12:00:00Z");
  assert(due({ github_checked_at: null, github_issue_state: null }, now));
  assert(!due({ github_checked_at: "2026-10-14T11:50:00Z", github_issue_state: "open" }, now));
  assert(due({ github_checked_at: "2026-10-14T11:40:00Z", github_issue_state: "open" }, now));
  assert(!due({ github_checked_at: "2026-10-14T00:00:00Z", github_issue_state: "closed" }, now));
  assertEquals(mergeLinks(
    [{ title: "Mine", url: "https://a.dev/x", kind: "link" }],
    [{ title: "Theirs", url: "https://A.dev/x", kind: "link" }, { title: "PR", url: "https://github.com/w/a/pull/1", kind: "pr" }],
  ).map((l) => l.title), ["Mine", "PR"]);
});

Deno.test("resultForDraft and the share_result note: the result rides along, mentions neutralized", () => {
  const text = resultForDraft({ note: "Shipped, thanks @val", links: [{ title: "PR #30", url: "https://github.com/w/a/pull/30", kind: "pr" }] }, "CSV export");
  assert(text.includes("What was asked: CSV export"));
  assert(text.includes("@​val"));
  assert(text.includes("- PR #\u200b30: https://github.com/w/a/pull/30"), "no issue references either");
  const note = intentNote("share_result", { name: "P" }, null, "full", text)!;
  assert(note.startsWith("Goal: a follow-up"));
  assert(note.includes("The result:\nWhat was asked: CSV export"));
  assertEquals(intentNote("discuss", { name: "P" }, null, "full", text)!.includes("The result"), false, "only share_result carries it");
});

async function testPem(): Promise<string> {
  const k = await crypto.subtle.generateKey(
    { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"]);
  const der = new Uint8Array(await crypto.subtle.exportKey("pkcs8", k.privateKey));
  return `-----BEGIN PRIVATE KEY-----\n${btoa(String.fromCharCode(...der))}\n-----END PRIVATE KEY-----`;
}

Deno.test("graphql: POST /graphql as the installation; partial data keeps its errors; no data throws (forbidden)", async () => {
  const bodies: unknown[] = [];
  let answer: unknown = { data: { organization: { projectsV2: { nodes: [] } } }, errors: [{ type: "FORBIDDEN", message: "Resource not accessible by integration" }] };
  const f = (input: string | URL | Request, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/access_tokens")) return Promise.resolve(Response.json({ token: "tok" }, { status: 201 }));
    assert(url.endsWith("/graphql"));
    assertEquals(new Headers(init?.headers).get("authorization"), "token tok");
    bodies.push(JSON.parse(String(init?.body)));
    return Promise.resolve(Response.json(answer));
  };
  const app = new GithubApp({ appId: "1", privateKeyPem: await testPem() }, f as typeof fetch);
  const r = await app.graphql(7, "query($login: String!) { x }", { login: "w" });
  assertEquals(r.errors[0].type, "FORBIDDEN");
  assertEquals(bodies[0], { query: "query($login: String!) { x }", variables: { login: "w" } });
  answer = { data: null, errors: [{ message: "Resource not accessible by integration" }] };
  const e = await assertRejects(() => app.graphql(7, "q"), GithubGraphqlError);
  assert(e.forbidden);
});

Deno.test("syncPlan: an uninstalled app is forgotten; suspension and selection follow GitHub; stale or forced lists re-read", () => {
  const now = Date.parse("2026-10-15T12:00:00Z");
  const live = (over: Partial<RawInstallation> = {}): RawInstallation => ({
    id: 5, account: { login: "Yahhi", id: 1, type: "User" }, repository_selection: "selected",
    created_at: "", updated_at: "", suspended_at: null, ...over,
  });
  const fresh = { repos_fetched_at: "2026-10-15T11:58:00Z" };
  const old = { repos_fetched_at: "2026-10-15T11:50:00Z" };
  assertEquals(syncPlan(null, fresh, false, now), { forget: true });
  assertEquals(syncPlan(live(), fresh, false, now), { forget: false, suspended_at: null, repository_selection: "selected", refresh: false });
  assertEquals(syncPlan(live(), old, false, now), { forget: false, suspended_at: null, repository_selection: "selected", refresh: true });
  assertEquals((syncPlan(live({ repository_selection: "all" }), fresh, true, now) as { refresh: boolean }).refresh, true, "forced");
  assertEquals(syncPlan(live({ suspended_at: "2026-10-15T10:00:00Z" }), old, true, now),
    { forget: false, suspended_at: "2026-10-15T10:00:00Z", repository_selection: "selected", refresh: false }, "suspended: no token to read with");
});
