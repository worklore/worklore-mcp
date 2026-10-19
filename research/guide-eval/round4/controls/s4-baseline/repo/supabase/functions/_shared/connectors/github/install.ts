// Linking a GitHub App installation to a Hearback project.
//
//   1. The app asks `github` {action: install_url}: a one-time state token
//      (32 random bytes, stored only as its SHA-256; founder, project, client,
//      15 minutes, single use) → https://github.com/apps/hearback-dev/installations/new?state=…
//   2. GitHub sends her back to `github-setup` with installation_id,
//      setup_action (install | update | request) and our state.
//   3. handleSetup(): checks the state, asks GitHub (as the app) about the
//      installation, makes sure it is hers, stores it with its repos and links
//      it to the project. Without a state (she changed repos in GitHub's
//      settings: setup_action=update) only an installation we already know
//      is refreshed.
//
// Why the ownership check: the setup URL's installation_id comes from the
// browser, so anyone with a valid state could paste another account's id.
// "Request user authorization during installation" is off (no user token),
// so an installation is accepted for a founder when (a) it is already hers
// or linked to a project she is a member of, (b) nobody has it yet and GitHub
// created or updated it within the last hour (she just installed it), or (c)
// it is installed on the personal GitHub account she signed in with.
// An installation someone else already has is never moved.

import type { InstallationRepo, RawInstallation } from "./app.ts";

export const STATE_TTL_MS = 15 * 60_000;
export const FRESH_INSTALL_MS = 60 * 60_000;
export type Client = "app" | "web";

const hex = (buf: ArrayBuffer) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");

/** A new state token (base64url, 43 chars) and the hash that is stored. */
export async function newStateToken(): Promise<{ token: string; hash: string }> {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  const token = btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  return { token, hash: await hashState(token) };
}

export async function hashState(token: string): Promise<string> {
  return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(token)));
}

export interface StateRow {
  founder_id: string; project_id: string; client: Client; expires_at: string; used_at: string | null;
}

export interface InstallationRow {
  installation_id: number; account_login: string; account_type: string; account_id: number | null;
  repository_selection: string; repos: InstallationRepo[]; repos_fetched_at: string;
  founder_id: string | null; suspended_at: string | null;
}

/** The database side of setup (Supabase in production, a map in tests). */
export interface InstallStore {
  findState(hash: string): Promise<StateRow | null>;
  /** Marks it used only if unused and unexpired; null when someone else got there first. */
  consumeState(hash: string, nowIso: string): Promise<StateRow | null>;
  getInstallation(id: number): Promise<InstallationRow | null>;
  upsertInstallation(row: InstallationRow): Promise<void>;
  linkProject(installationId: number, projectId: string, founderId: string): Promise<void>;
  /** Is the founder a member of a project this installation is linked to? */
  memberOfLinkedProject(installationId: number, founderId: string): Promise<boolean>;
  /** The numeric GitHub user id she signed in with, if she used GitHub sign-in. */
  founderGithubId(founderId: string): Promise<number | null>;
}

/** GitHub as the app sees it. */
export interface InstallGithub {
  installation(id: number): Promise<RawInstallation | null>;
  repos(id: number): Promise<InstallationRepo[]>;
}

export type SetupReason =
  | "bad_request" | "requested" | "missing_state" | "bad_state" | "expired_state" | "used_state"
  | "unknown_installation" | "not_yours" | "github_error";

export type SetupOutcome =
  | { ok: true; client: Client | null; installation_id: number; account_login: string; repos: number; project_id: string | null; refreshed_only: boolean }
  | { ok: false; client: Client | null; reason: SetupReason };

export const SETUP_MESSAGES: Record<SetupReason, string> = {
  bad_request: "GitHub didn't say which installation this is.",
  requested: "Your organization's owner has to approve the Hearback.dev app first. Once they do, connect GitHub again in Hearback.",
  missing_state: "We don't know which Hearback project this is for. Open Hearback and tap Connect GitHub there.",
  bad_state: "This link isn't from Hearback, or it was changed. Open Hearback and tap Connect GitHub again.",
  expired_state: "This link expired (they last 15 minutes). Open Hearback and tap Connect GitHub again.",
  used_state: "This link was already used. Open Hearback and tap Connect GitHub again.",
  unknown_installation: "We couldn't find that installation of Hearback.dev on GitHub.",
  not_yours: "This GitHub installation is linked to another Hearback account, or it wasn't just installed by you. Open Hearback and tap Connect GitHub again.",
  github_error: "GitHub didn't answer. Try again in a minute.",
};

function installationRow(inst: RawInstallation, repos: InstallationRepo[], founderId: string | null, now: Date): InstallationRow {
  return {
    installation_id: inst.id,
    account_login: inst.account?.login ?? "",
    account_type: inst.account?.type ?? "User",
    account_id: inst.account?.id ?? null,
    repository_selection: inst.repository_selection,
    repos,
    repos_fetched_at: now.toISOString(),
    founder_id: founderId,
    suspended_at: inst.suspended_at,
  };
}

/** May this founder take this installation? See the header. */
export async function mayClaim(store: InstallStore, inst: RawInstallation, existing: InstallationRow | null, founderId: string, now: Date): Promise<boolean> {
  if (existing?.founder_id === founderId) return true;
  if (existing && await store.memberOfLinkedProject(inst.id, founderId)) return true;
  if (existing?.founder_id) return false; // someone else's: never moved
  const touched = Math.max(Date.parse(inst.created_at) || 0, Date.parse(inst.updated_at) || 0);
  if (now.getTime() - touched <= FRESH_INSTALL_MS) return true;
  if (inst.account?.type === "User") {
    const gh = await store.founderGithubId(founderId);
    if (gh !== null && gh === inst.account.id) return true;
  }
  return false;
}

/** GitHub's redirect to the Setup URL → what happened. Never throws for bad input. */
export async function handleSetup(params: URLSearchParams, store: InstallStore, gh: InstallGithub, now = new Date()): Promise<SetupOutcome> {
  const action = params.get("setup_action") ?? "install";
  const rawId = params.get("installation_id") ?? "";
  const stateToken = params.get("state");
  let client: Client | null = null;
  let state: StateRow | null = null;

  if (stateToken) {
    const hash = await hashState(stateToken);
    const row = await store.findState(hash);
    if (!row) return { ok: false, client, reason: "bad_state" };
    client = row.client;
    if (row.used_at) return { ok: false, client, reason: "used_state" };
    if (Date.parse(row.expires_at) <= now.getTime()) return { ok: false, client, reason: "expired_state" };
    state = await store.consumeState(hash, now.toISOString());
    if (!state) return { ok: false, client, reason: "used_state" };
  }
  if (action === "request") return { ok: false, client, reason: "requested" };
  if (!/^\d{1,15}$/.test(rawId)) return { ok: false, client, reason: "bad_request" };
  const id = Number(rawId);

  if (!state) {
    // Repos changed from GitHub's settings ("redirect on update"): refresh what we know, link nothing.
    if (action !== "update") return { ok: false, client, reason: "missing_state" };
    const existing = await store.getInstallation(id);
    if (!existing) return { ok: false, client, reason: "unknown_installation" };
    let inst: RawInstallation | null;
    let repos: InstallationRepo[];
    try {
      inst = await gh.installation(id);
      if (!inst) return { ok: false, client, reason: "unknown_installation" };
      repos = await gh.repos(id);
    } catch {
      return { ok: false, client, reason: "github_error" };
    }
    await store.upsertInstallation(installationRow(inst, repos, existing.founder_id, now));
    return { ok: true, client, installation_id: id, account_login: inst.account?.login ?? "", repos: repos.length, project_id: null, refreshed_only: true };
  }

  let inst: RawInstallation | null;
  try {
    inst = await gh.installation(id);
  } catch {
    return { ok: false, client, reason: "github_error" };
  }
  if (!inst) return { ok: false, client, reason: "unknown_installation" };
  const existing = await store.getInstallation(id);
  if (!await mayClaim(store, inst, existing, state.founder_id, now)) return { ok: false, client, reason: "not_yours" };
  let repos: InstallationRepo[];
  try {
    repos = await gh.repos(id);
  } catch {
    return { ok: false, client, reason: "github_error" };
  }
  await store.upsertInstallation(installationRow(inst, repos, existing?.founder_id ?? state.founder_id, now));
  await store.linkProject(id, state.project_id, state.founder_id);
  return { ok: true, client, installation_id: id, account_login: inst.account?.login ?? "", repos: repos.length, project_id: state.project_id, refreshed_only: false };
}

export const APP_RETURN = "dev.hearback.app://github-installed";
export const PAGE_RETURN = "https://hearback.dev/github-installed.html";

/** Where the browser goes after setup: the app's scheme on success from the app, else the static page. */
export function setupRedirect(o: SetupOutcome): string {
  if (o.ok && o.client === "app") return `${APP_RETURN}?ok=1&installation_id=${o.installation_id}`;
  const q = new URLSearchParams({ ok: o.ok ? "1" : "0" });
  if (o.client) q.set("client", o.client);
  if (o.ok) q.set("account", o.account_login);
  else q.set("reason", o.reason);
  return `${PAGE_RETURN}?${q}`;
}
