// The Hearback.dev GitHub App (docs/ARCHITECTURE.md › GitHub App).
//
// Nothing secret is stored per user. The server signs a short app JWT with
// the app's private key (function secret GITHUB_APP_PRIVATE_KEY, PKCS#8 PEM)
// and exchanges it for an installation token when it needs one; tokens live
// in this isolate's memory for at most 50 minutes (GitHub gives 60).
//
//   appJwt()                     RS256 JWT, iat 60 s in the past, exp +9 min
//   installationToken(id)        POST /app/installations/{id}/access_tokens (cached)
//   GithubApi                    tiny REST client: as the app or as an installation

const API = "https://api.github.com";
const UA = "hearback/0.1 (+https://hearback.dev)";
export const APP_SLUG = "hearback-dev";
/** A token younger than this is reused. */
export const TOKEN_TTL_MS = 50 * 60_000;

type Fetch = typeof fetch;

export class GithubApiError extends Error {
  constructor(readonly status: number, readonly path: string, readonly body: string, readonly resetAt: string | null = null) {
    super(`GitHub ${status} on ${path.split("?")[0]}`);
  }
  get rateLimited() { return this.resetAt !== null; }
}

/** One GraphQL error; `type` FORBIDDEN / NOT_FOUND matter (missing permission, no such board). */
export interface GraphqlError { type?: string; message: string; path?: (string | number)[] }

export class GithubGraphqlError extends Error {
  constructor(readonly errors: GraphqlError[]) {
    super(`GitHub GraphQL: ${errors.map((e) => e.type ?? e.message).join(", ").slice(0, 200) || "no data"}`);
  }
  /** The app lacks a permission (e.g. organization projects). */
  get forbidden() { return this.errors.some(isForbidden); }
  get notFound() { return this.errors.some((e) => e.type === "NOT_FOUND"); }
}

export const isForbidden = (e: GraphqlError) =>
  e.type === "FORBIDDEN" || /not accessible by integration/i.test(e.message);

const b64url = (bytes: Uint8Array) =>
  btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const b64urlJson = (v: unknown) => b64url(new TextEncoder().encode(JSON.stringify(v)));

/** PKCS#8 PEM ("BEGIN PRIVATE KEY") → CryptoKey for RS256. A PKCS#1 key is refused with a hint. */
export async function importAppKey(pem: string): Promise<CryptoKey> {
  if (/BEGIN RSA PRIVATE KEY/.test(pem)) {
    throw new Error("GitHub App key is PKCS#1; convert it: openssl pkcs8 -topk8 -nocrypt");
  }
  const body = pem.replace(/-----(BEGIN|END) PRIVATE KEY-----/g, "").replace(/\s+/g, "");
  if (!body) throw new Error("GitHub App key is empty");
  const der = Uint8Array.from(atob(body), (c) => c.charCodeAt(0));
  return await crypto.subtle.importKey("pkcs8", der, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
}

/** The app's JWT (RS256). `nowMs` for tests. */
export async function appJwt(appId: string, key: CryptoKey, nowMs = Date.now()): Promise<string> {
  const now = Math.floor(nowMs / 1000);
  // iat 60 s back against clock drift; exp ≤ 10 min (GitHub's maximum).
  const head = b64urlJson({ alg: "RS256", typ: "JWT" });
  const claims = b64urlJson({ iat: now - 60, exp: now + 540, iss: appId });
  const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(`${head}.${claims}`));
  return `${head}.${claims}.${b64url(new Uint8Array(sig))}`;
}

export interface AppCredentials { appId: string; privateKeyPem: string }

export function appCredentials(): AppCredentials | null {
  const appId = Deno.env.get("GITHUB_APP_ID");
  const privateKeyPem = Deno.env.get("GITHUB_APP_PRIVATE_KEY");
  return appId && privateKeyPem ? { appId, privateKeyPem: privateKeyPem.replace(/\\n/g, "\n") } : null;
}

async function request<T>(fetchFn: Fetch, auth: string, method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetchFn(`${API}${path}`, {
    method,
    headers: {
      authorization: auth,
      accept: "application/vnd.github+json",
      "x-github-api-version": "2022-11-28",
      "user-agent": UA,
      ...(body !== undefined ? { "content-type": "application/json" } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(15_000),
  });
  const text = await res.text();
  if (!res.ok) {
    const limited = (res.status === 403 || res.status === 429) &&
      (res.headers.get("x-ratelimit-remaining") === "0" || !!res.headers.get("retry-after"));
    const reset = Number(res.headers.get("x-ratelimit-reset") ?? 0);
    throw new GithubApiError(res.status, path, text.slice(0, 500),
      limited ? (reset ? new Date(reset * 1000).toISOString() : "") : null);
  }
  return (text ? JSON.parse(text) : null) as T;
}

/**
 * The app's view of GitHub. One per isolate (`githubApp()`), so the token
 * cache is shared by every request the isolate serves.
 */
export class GithubApp {
  private key: Promise<CryptoKey> | null = null;
  private tokens = new Map<number, { token: string; at: number }>();
  /** Counts for tests: how many tokens were minted. */
  minted = 0;

  constructor(private creds: AppCredentials, private fetchFn: Fetch = fetch, private now: () => number = Date.now) {}

  async jwt(): Promise<string> {
    this.key ??= importAppKey(this.creds.privateKeyPem);
    return await appJwt(this.creds.appId, await this.key, this.now());
  }

  /** As the app (JWT): /app, /app/installations/{id}. */
  async asApp<T>(method: string, path: string, body?: unknown): Promise<T> {
    return await request<T>(this.fetchFn, `Bearer ${await this.jwt()}`, method, path, body);
  }

  /** An installation token, reused for up to 50 minutes. */
  async installationToken(installationId: number): Promise<string> {
    const hit = this.tokens.get(installationId);
    if (hit && this.now() - hit.at < TOKEN_TTL_MS) return hit.token;
    const r = await this.asApp<{ token: string }>("POST", `/app/installations/${installationId}/access_tokens`);
    this.minted++;
    this.tokens.set(installationId, { token: r.token, at: this.now() });
    return r.token;
  }

  forget(installationId: number) { this.tokens.delete(installationId); }

  /** As an installation: repos, issues, search. A 401 drops the cached token and retries once. */
  async asInstallation<T>(installationId: number, method: string, path: string, body?: unknown): Promise<T> {
    try {
      return await request<T>(this.fetchFn, `token ${await this.installationToken(installationId)}`, method, path, body);
    } catch (e) {
      if (e instanceof GithubApiError && e.status === 401) {
        this.forget(installationId);
        return await request<T>(this.fetchFn, `token ${await this.installationToken(installationId)}`, method, path, body);
      }
      throw e;
    }
  }

  /**
   * GraphQL as an installation (boards live only there). A partial answer
   * comes back with its errors: a field the app may not read is null, the
   * rest is data. No data at all → GithubGraphqlError.
   */
  async graphql<T>(installationId: number, query: string, variables: Record<string, unknown> = {}): Promise<{ data: T; errors: GraphqlError[] }> {
    const r = await this.asInstallation<{ data?: T | null; errors?: GraphqlError[] }>(installationId, "POST", "/graphql", { query, variables });
    const errors = r?.errors ?? [];
    if (!r?.data) throw new GithubGraphqlError(errors);
    return { data: r.data, errors };
  }

  /** Every repo the installation can reach (paged, ≤ 300). */
  async installationRepos(installationId: number): Promise<InstallationRepo[]> {
    const out: InstallationRepo[] = [];
    for (let page = 1; page <= 3; page++) {
      const r = await this.asInstallation<{ total_count: number; repositories: RawRepo[] }>(
        installationId, "GET", `/installation/repositories?per_page=100&page=${page}`);
      out.push(...r.repositories.map(repoFromApi));
      if (out.length >= r.total_count || r.repositories.length < 100) break;
    }
    return out;
  }
}

let _app: GithubApp | null | undefined;
/** The isolate's app client; null when the secrets are not set. */
export function githubApp(): GithubApp | null {
  if (_app !== undefined) return _app;
  const creds = appCredentials();
  return _app = creds ? new GithubApp(creds) : null;
}

export interface RawRepo {
  full_name: string; private: boolean; default_branch?: string; open_issues_count?: number;
  pushed_at?: string | null; description?: string | null; html_url?: string; archived?: boolean; has_issues?: boolean;
}

/** What Hearback keeps of a repo (github_installations.repos). */
export interface InstallationRepo {
  full_name: string; private: boolean; default_branch: string | null; open_issues: number;
  pushed_at: string | null; description: string | null; archived: boolean; has_issues: boolean;
}

export const repoFromApi = (r: RawRepo): InstallationRepo => ({
  full_name: r.full_name, private: !!r.private, default_branch: r.default_branch ?? null,
  open_issues: r.open_issues_count ?? 0, pushed_at: r.pushed_at ?? null,
  description: r.description ? r.description.slice(0, 200) : null,
  archived: !!r.archived, has_issues: r.has_issues !== false,
});

/** The installation as GET /app/installations/{id} returns it (the fields used). */
export interface RawInstallation {
  id: number;
  account: { login: string; id: number; type: string } | null;
  repository_selection: "all" | "selected";
  created_at: string; updated_at: string; suspended_at: string | null;
  html_url?: string;
}

/** Where she adds or removes repos: her own settings, or the org's. */
export function manageUrl(inst: { installation_id: number; account_login: string; account_type: string }): string {
  return inst.account_type === "Organization"
    ? `https://github.com/organizations/${encodeURIComponent(inst.account_login)}/settings/installations/${inst.installation_id}`
    : `https://github.com/settings/installations/${inst.installation_id}`;
}

export const installUrl = (state: string) =>
  `https://github.com/apps/${APP_SLUG}/installations/new?state=${encodeURIComponent(state)}`;
