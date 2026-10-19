// GitHub as a SOURCE connector (docs/ARCHITECTURE.md › Sources: voice and
// knowledge). It reads the folder `projects.github_folder` (default
// `hearback/`) of the project's linked repo (`projects.github_repo`): every
// .md/.markdown/.txt file becomes a quotable knowledge document (GitHub blob
// URL, dated by its last commit) and its paragraphs/messages become voice-
// sample candidates. Issues: issues.ts + functions/github (the GitHub App).
//
// With the Hearback.dev GitHub App installed on the repo (an installation
// linked to the project), requests carry an installation token (5,000/hour,
// private repos work; file bodies come from the contents API). A private
// repo's files are `background` knowledge (context only, never quoted or
// linked: readers couldn't open the link). Without an installation: public
// repos only, unauthenticated (60 API requests/hour per IP):
//   - conditional requests (ETag → 304 costs nothing): repo metadata and the
//     branch head; an unchanged head means nothing to do;
//   - the tree (one request) → files whose blob sha changed since last run;
//   - file bodies from raw.githubusercontent.com (outside the API limit);
//   - one API request per changed file for its commit date (capped per run).
// A 404 on the repo means private or missing (or not in the installation's
// repos): status needs_auth. Rate limit hit → status rate_limited.

import type { Connector, ProjectSourceRow, SourceBatch, SourceContext, SourceDocument, OwnWriting } from "../../core/types.ts";
import { installationTokenForRepo } from "../../server/github.ts";
import { documentFromFile, folderPrefix, GITHUB_CAPS, planGithubSync, TreeEntry, writingFromFile } from "./split.ts";

const API = "https://api.github.com";
const RAW = "https://raw.githubusercontent.com";
const UA = "hearback/0.1 (+https://hearback.dev)";
const REPO_RE = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;

export class GithubRateLimited extends Error {
  constructor(readonly resetAt: string | null) { super(`GitHub rate limit reached${resetAt ? ` until ${resetAt}` : ""}`); }
}

type Fetch = typeof fetch;

/** GitHub REST client with ETag caching in the source state; unauthenticated unless given an installation token. */
export class GithubPublic {
  requests = 0;
  constructor(private etags: Record<string, { etag: string; value: unknown }>, private fetchFn: Fetch = fetch, private token: string | null = null) {}

  async get<T>(path: string, opts: { accept?: string; cache?: boolean } = {}): Promise<{ data: T | null; status: number; cached: boolean }> {
    const cached = opts.cache ? this.etags[path] : undefined;
    const headers: Record<string, string> = { "user-agent": UA, accept: opts.accept ?? "application/vnd.github+json", "x-github-api-version": "2022-11-28" };
    if (cached) headers["if-none-match"] = cached.etag;
    if (this.token) headers.authorization = `token ${this.token}`;
    this.requests++;
    const res = await this.fetchFn(`${API}${path}`, { headers, signal: AbortSignal.timeout(15_000) });
    if (res.status === 304 && cached) { await res.body?.cancel(); return { data: cached.value as T, status: 304, cached: true }; }
    if ((res.status === 403 || res.status === 429) && (res.headers.get("x-ratelimit-remaining") === "0" || res.headers.get("retry-after"))) {
      await res.body?.cancel();
      const reset = Number(res.headers.get("x-ratelimit-reset") ?? 0);
      throw new GithubRateLimited(reset ? new Date(reset * 1000).toISOString() : null);
    }
    if (res.status === 404) { await res.body?.cancel(); return { data: null, status: 404, cached: false }; }
    if (!res.ok) { await res.body?.cancel(); throw new Error(`GitHub ${res.status} on ${path.split("?")[0]}`); }
    const text = await res.text();
    const data = (opts.accept?.includes("sha") ? text.trim() : JSON.parse(text)) as T;
    const etag = res.headers.get("etag");
    if (opts.cache && etag) this.etags[path] = { etag, value: data };
    return { data, status: res.status, cached: false };
  }

  async raw(repo: string, ref: string, path: string): Promise<string> {
    const enc = path.split("/").map(encodeURIComponent).join("/");
    if (this.token) {
      // Private repos: raw.githubusercontent.com doesn't take installation tokens reliably; the contents API does.
      this.requests++;
      const res = await this.fetchFn(`${API}/repos/${repo}/contents/${enc}?ref=${encodeURIComponent(ref)}`, {
        headers: { "user-agent": UA, accept: "application/vnd.github.raw", authorization: `token ${this.token}`, "x-github-api-version": "2022-11-28" },
        signal: AbortSignal.timeout(15_000),
      });
      if (!res.ok) { await res.body?.cancel(); throw new Error(`contents ${res.status} ${path}`); }
      return await res.text();
    }
    const res = await this.fetchFn(`${RAW}/${repo}/${ref}/${path.split("/").map(encodeURIComponent).join("/")}`,
      { headers: { "user-agent": UA }, signal: AbortSignal.timeout(15_000) });
    if (!res.ok) { await res.body?.cancel(); throw new Error(`raw ${res.status} ${path}`); }
    return await res.text();
  }
}

export async function githubFolderSource(project: ProjectSourceRow, ctx: SourceContext, fetchFn: Fetch = fetch, token: string | null = null): Promise<SourceBatch> {
  const repo = (project.github_repo ?? "").trim();
  if (!repo) return { status: "empty", message: "No GitHub repo linked." };
  if (!REPO_RE.test(repo)) return { status: "error", message: `Not a repo name: ${repo}` };
  const folder = project.github_folder ?? "hearback";
  const prev = ctx.state as { etags?: Record<string, { etag: string; value: unknown }>; files?: Record<string, string>; head?: string; folder?: string };
  const etags = { ...(prev.etags ?? {}) };
  // A different folder than last run: forget file SHAs so everything is read once.
  const files = prev.folder === folder ? { ...(prev.files ?? {}) } : {};
  const gh = new GithubPublic(etags, fetchFn, token);
  let branch: string | undefined = (prev as { branch?: string }).branch;
  const state = () => ({ etags, files, head: prev.head, folder, branch });
  try {
    const meta = await gh.get<{ default_branch: string; private?: boolean }>(`/repos/${repo}`, { cache: true });
    if (!meta.data) {
      return {
        status: "needs_auth",
        message: token
          ? `Hearback.dev can't read ${repo}. Add it to the app's repositories on GitHub (Project › Ideas go to › Manage repositories).`
          : `Can't read ${repo}: it is private or doesn't exist. Connect GitHub in Project and give Hearback.dev access to it.`,
        state: state(),
      };
    }
    branch = meta.data.default_branch;
    // A private repo's files can't be opened by the people she replies to: context only.
    const label = meta.data.private ? "background" as const : "quotable" as const;
    const head = await gh.get<string>(`/repos/${repo}/commits/${encodeURIComponent(branch)}`, { accept: "application/vnd.github.sha", cache: true });
    if (!head.data) return { status: "empty", message: `${repo} has no commits.`, state: state() };
    if (head.cached && prev.head === head.data && prev.folder === folder) {
      return { status: "ok", message: null, state: state(), stats: { unchanged_head: 1, api_requests: gh.requests } };
    }
    const tree = await gh.get<{ tree: TreeEntry[]; truncated?: boolean }>(`/repos/${repo}/git/trees/${head.data}?recursive=1`);
    const plan = planGithubSync(tree.data?.tree ?? [], folder, files);
    const inFolder = plan.read.length + plan.unchanged.length + plan.skipped.length;
    const documents: SourceDocument[] = [];
    const writing: OwnWriting[] = [];
    let deferred = 0, limited: GithubRateLimited | null = null;
    for (const f of plan.read) {
      if (limited || Date.now() > ctx.deadline) { deferred++; continue; }
      try {
        const md = await gh.raw(repo, head.data, f.path);
        const c = await gh.get<{ commit: { committer: { date: string } } }[]>(
          `/repos/${repo}/commits?path=${encodeURIComponent(f.path)}&sha=${encodeURIComponent(branch)}&per_page=1`);
        const date = c.data?.[0]?.commit?.committer?.date ?? new Date().toISOString();
        const url = `https://github.com/${repo}/blob/${encodeURIComponent(branch)}/${f.path.split("/").map(encodeURIComponent).join("/")}`;
        documents.push({ ...documentFromFile(md, { path: f.path, url, date }), label });
        const room = GITHUB_CAPS.maxWritingPerRun - writing.length;
        if (room > 0) writing.push(...writingFromFile(md, { repo, path: f.path, url, date }).slice(0, room));
        files[f.path] = f.sha;
      } catch (e) {
        if (e instanceof GithubRateLimited) { limited = e; deferred++; continue; }
        throw e;
      }
    }
    const later = plan.skipped.filter((s) => s.reason.startsWith("run_")).length + deferred;
    // Only an all-read folder may skip the next run on an unchanged head.
    if (!later) prev.head = head.data;
    const tooLarge = plan.skipped.filter((s) => s.reason === "too_large").map((s) => s.path);
    const overCap = plan.skipped.filter((s) => s.reason === "over_file_cap").length;
    const notes = [
      !inFolder ? `No .md or .txt files in ${folderPrefix(folder) || "the repo root"} yet.` : "",
      tooLarge.length ? `Over ${GITHUB_CAPS.maxFileBytes / 1000} KB, skipped: ${tooLarge.slice(0, 3).join(", ")}${tooLarge.length > 3 ? "…" : ""}.` : "",
      overCap ? `Only the first ${GITHUB_CAPS.maxFiles} files are read (${overCap} more).` : "",
      later ? `${later} file(s) left for the next run.` : "",
      limited ? limited.message + "." : "",
      tree.data?.truncated ? "The repo is very large; part of the tree was not listed." : "",
    ].filter(Boolean);
    return {
      documents, writing, state: state(), status: limited ? "rate_limited" : inFolder ? "ok" : "empty", message: notes.join(" ") || null,
      stats: { files: inFolder, read: documents.length, unchanged: plan.unchanged.length, skipped: plan.skipped.length, api_requests: gh.requests, authenticated: token ? 1 : 0, private: meta.data.private ? 1 : 0 },
    };
  } catch (e) {
    if (e instanceof GithubRateLimited) return { status: "rate_limited", message: e.message, state: state() };
    return { status: "error", message: (e as Error).message.slice(0, 200), state: state() };
  }
}

export const githubConnector: Connector = {
  id: "github",
  label: "GitHub",
  auth: "none", // public repos without anything; with the GitHub App installed: an installation token (private repos too)
  accountAuth: "none",
  needsSecret: false,
  // A source, not a network to listen on: the CONNECTORS flag doesn't apply.
  enabled: () => true,
  schedule: null,
  rateLimit: { minIntervalMs: 0, maxRequestsPerRun: 2 + GITHUB_CAPS.maxChangedPerRun + 2, on429: "backoff_account" },
  reply: { mode: "none", maxGraphemes: null },
  projectSource: async (project, ctx) => {
    let token: string | null = null;
    if (project.github_repo) {
      try {
        token = await installationTokenForRepo(project.id, project.github_repo.trim());
      } catch (e) {
        console.error("github source: no installation token:", (e as Error).message.slice(0, 120));
      }
    }
    return githubFolderSource(project, ctx, fetch, token);
  },
};
