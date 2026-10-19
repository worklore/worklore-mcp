// Database side of the GitHub App: the InstallStore for github-setup, and
// which installation can reach a project's repo (for the repo picker, issues
// and the GitHub source). docs/ARCHITECTURE.md › GitHub App.

import { GithubApiError, githubApp, GithubApp, GithubGraphqlError, InstallationRepo, isForbidden, manageUrl, RawInstallation } from "../connectors/github/app.ts";
import { Board, BOARD_ITEMS, BoardItem, MAX_BOARD_PAGES, ORG_BOARDS, parseBoardItems, parseBoards } from "../connectors/github/boards.ts";
import type { InstallationRow, InstallStore, StateRow } from "../connectors/github/install.ts";
import { admin } from "./ctx.ts";

export function supabaseInstallStore(): InstallStore {
  const db = admin();
  return {
    async findState(hash) {
      const { data, error } = await db.from("github_install_states").select("founder_id, project_id, client, expires_at, used_at")
        .eq("token_sha256", hash).maybeSingle();
      if (error) throw error;
      return data as StateRow | null;
    },
    async consumeState(hash, nowIso) {
      const { data, error } = await db.from("github_install_states").update({ used_at: nowIso })
        .eq("token_sha256", hash).is("used_at", null).gt("expires_at", nowIso)
        .select("founder_id, project_id, client, expires_at, used_at").maybeSingle();
      if (error) throw error;
      return data as StateRow | null;
    },
    async getInstallation(id) {
      const { data, error } = await db.from("github_installations").select("*").eq("installation_id", id).maybeSingle();
      if (error) throw error;
      return data as InstallationRow | null;
    },
    async upsertInstallation(row) {
      const { error } = await db.from("github_installations").upsert({ ...row, updated_at: new Date().toISOString() }, { onConflict: "installation_id" });
      if (error) throw error;
    },
    async linkProject(installationId, projectId, founderId) {
      const { error } = await db.from("github_installation_projects")
        .upsert({ installation_id: installationId, project_id: projectId, linked_by: founderId }, { onConflict: "installation_id,project_id", ignoreDuplicates: true });
      if (error) throw error;
    },
    async memberOfLinkedProject(installationId, founderId) {
      const { data: links } = await db.from("github_installation_projects").select("project_id").eq("installation_id", installationId);
      const ids = (links ?? []).map((l) => l.project_id);
      if (!ids.length) return false;
      const { data } = await db.from("project_members").select("project_id").eq("founder_id", founderId).in("project_id", ids).limit(1);
      return !!data?.length;
    },
    async founderGithubId(founderId) {
      const { data } = await db.auth.admin.getUserById(founderId);
      const ident = data?.user?.identities?.find((i) => i.provider === "github");
      const id = Number(ident?.identity_data?.provider_id ?? ident?.identity_data?.sub ?? ident?.id);
      return Number.isFinite(id) && id > 0 ? id : null;
    },
  };
}

/** GitHub calls github-setup needs, as the app. */
export function installGithub(app: GithubApp) {
  return {
    async installation(id: number): Promise<RawInstallation | null> {
      try {
        return await app.asApp<RawInstallation>("GET", `/app/installations/${id}`);
      } catch (e) {
        if ((e as { status?: number }).status === 404) return null;
        throw e;
      }
    },
    repos: (id: number) => app.installationRepos(id),
  };
}

export interface ProjectInstallation extends InstallationRow { manage_url: string }

/** Installations linked to a project (live ones first). */
export async function projectInstallations(projectId: string): Promise<ProjectInstallation[]> {
  const db = admin();
  const { data: links, error } = await db.from("github_installation_projects").select("installation_id").eq("project_id", projectId);
  if (error) throw error;
  const ids = (links ?? []).map((l) => l.installation_id);
  if (!ids.length) return [];
  const { data } = await db.from("github_installations").select("*").in("installation_id", ids);
  return ((data ?? []) as InstallationRow[])
    .sort((a, b) => Number(!!a.suspended_at) - Number(!!b.suspended_at))
    .map((i) => ({ ...i, manage_url: manageUrl(i) }));
}

const sameRepo = (a: string, b: string) => a.toLowerCase() === b.toLowerCase();

/** Re-reads an installation's repos from GitHub and stores them. */
export async function refreshInstallationRepos(app: GithubApp, installationId: number): Promise<InstallationRepo[]> {
  const repos = await app.installationRepos(installationId);
  await admin().from("github_installations").update({ repos, repos_fetched_at: new Date().toISOString(), updated_at: new Date().toISOString() })
    .eq("installation_id", installationId);
  return repos;
}

/** A stored repo list older than this is re-read from GitHub when the app asks for status. */
export const REPOS_FRESH_MS = 5 * 60_000;

/**
 * Pure. A stored installation against what GitHub says now: gone (she
 * uninstalled the app) → forget it with its repos; otherwise its suspension
 * and repo selection as GitHub has them, and whether to re-read the repos.
 */
export function syncPlan(live: RawInstallation | null, row: Pick<InstallationRow, "repos_fetched_at">, force: boolean, now = Date.now()):
  { forget: true } | { forget: false; suspended_at: string | null; repository_selection: string; refresh: boolean } {
  if (!live) return { forget: true };
  const stale = !row.repos_fetched_at || now - Date.parse(row.repos_fetched_at) >= REPOS_FRESH_MS;
  return {
    forget: false, suspended_at: live.suspended_at ?? null, repository_selection: live.repository_selection,
    refresh: !live.suspended_at && (force || stale),
  };
}

/**
 * Brings the project's stored installations in line with GitHub (there is no
 * webhook): an uninstalled one is deleted with its repo list and project
 * links, a suspended one is marked, and repo lists older than five minutes
 * (or all, with `force`) are re-read, so only repos she grants now are shown.
 * A GitHub error leaves that installation as stored.
 */
export async function syncProjectInstallations(projectId: string, app: GithubApp, force = false): Promise<void> {
  const db = admin();
  const gh = installGithub(app);
  for (const row of await projectInstallations(projectId)) {
    try {
      const plan = syncPlan(await gh.installation(row.installation_id), row, force);
      if (plan.forget) {
        app.forget(row.installation_id);
        const { error } = await db.from("github_installations").delete().eq("installation_id", row.installation_id);
        if (error) throw error;
        continue;
      }
      await db.from("github_installations").update({
        suspended_at: plan.suspended_at, repository_selection: plan.repository_selection, updated_at: new Date().toISOString(),
      }).eq("installation_id", row.installation_id);
      if (plan.refresh) await refreshInstallationRepos(app, row.installation_id);
    } catch (e) {
      console.error("github: sync installation:", (e as Error).message.slice(0, 160));
    }
  }
}

/**
 * The installation of this project that can reach `repo` (owner/name), or
 * null. Looks in the cached repo lists first; an installation on the repo's
 * owner whose cache misses it is refreshed once (she may have just added it).
 */
export async function installationForRepo(projectId: string, repo: string, app: GithubApp | null = githubApp()):
  Promise<{ installation: ProjectInstallation; repo: InstallationRepo } | null> {
  if (!app || !repo) return null;
  const insts = (await projectInstallations(projectId)).filter((i) => !i.suspended_at);
  for (const i of insts) {
    const r = (i.repos ?? []).find((x) => sameRepo(x.full_name, repo));
    if (r) return { installation: i, repo: r };
  }
  const owner = repo.split("/")[0];
  for (const i of insts.filter((x) => sameRepo(x.account_login, owner))) {
    try {
      const repos = await refreshInstallationRepos(app, i.installation_id);
      const r = repos.find((x) => sameRepo(x.full_name, repo));
      if (r) return { installation: { ...i, repos }, repo: r };
    } catch (e) {
      console.error("github: refresh repos failed:", (e as Error).message.slice(0, 120));
    }
  }
  return null;
}

/** An installation token that can read `repo` for this project, or null (then the source reads it unauthenticated). */
export async function installationTokenForRepo(projectId: string, repo: string): Promise<string | null> {
  const app = githubApp();
  if (!app) return null;
  const reach = await installationForRepo(projectId, repo, app);
  return reach ? await app.installationToken(reach.installation.installation_id) : null;
}

// ------------------------------------------------------------------ boards (Projects v2, read-only)

/** One organization installation's boards, or why it can't list them. */
export interface OrgBoards {
  login: string;
  installation_id: number;
  manage_url: string;
  /** ok; no_permission: the app hasn't been granted "Organization projects: read" there. */
  access: "ok" | "no_permission" | "error";
  boards: Board[];
}

/** The boards of every organization linked to the project (personal accounts can't share boards with an app). */
export async function projectBoards(projectId: string, app: GithubApp): Promise<{ orgs: OrgBoards[]; personal: string[] }> {
  const insts = (await projectInstallations(projectId)).filter((i) => !i.suspended_at);
  const orgs: OrgBoards[] = [];
  for (const i of insts.filter((x) => x.account_type === "Organization")) {
    const base = { login: i.account_login, installation_id: i.installation_id, manage_url: i.manage_url };
    try {
      const { data, errors } = await app.graphql(i.installation_id, ORG_BOARDS, { login: i.account_login });
      const boards = parseBoards(i.account_login, data);
      orgs.push({ ...base, access: !boards.length && errors.some(isForbidden) ? "no_permission" : "ok", boards });
    } catch (e) {
      const forbidden = e instanceof GithubGraphqlError ? e.forbidden : e instanceof GithubApiError && e.status === 403;
      if (!forbidden) console.error("github: boards:", (e as Error).message.slice(0, 160));
      orgs.push({ ...base, access: forbidden ? "no_permission" : "error", boards: [] });
    }
  }
  return { orgs, personal: insts.filter((x) => x.account_type !== "Organization").map((x) => x.account_login) };
}

/** The project's installation on this organization (it reads the org's boards), or null. */
export async function orgInstallation(projectId: string, owner: string): Promise<ProjectInstallation | null> {
  return (await projectInstallations(projectId))
    .find((i) => !i.suspended_at && i.account_type === "Organization" && sameRepo(i.account_login, owner)) ?? null;
}

/** Every item on the board, up to MAX_BOARD_PAGES pages (for the duplicate check). */
export async function readBoardItems(app: GithubApp, installationId: number, boardId: string): Promise<BoardItem[]> {
  const out: BoardItem[] = [];
  let after: string | null = null;
  for (let page = 0; page < MAX_BOARD_PAGES; page++) {
    const { data } = await app.graphql(installationId, BOARD_ITEMS, { id: boardId, after });
    const r = parseBoardItems(data);
    out.push(...r.items);
    if (!r.next) break;
    after = r.next;
  }
  return out;
}
