// Bluesky (AT Protocol) over plain XRPC: resolve the account's PDS, log in with
// the app password once, keep the session (access + refresh JWT) in Vault and
// refresh it (createSession is limited to 30 per 5 min / 300 per day), read
// notifications and threads, post replies with facets. Rate limits: on 429 the
// account gets a backoff_until from the ratelimit-reset header.

import { admin } from "../../server/ctx.ts";
import { HttpError } from "../../server/http.ts";

const ENTRYWAY = "https://bsky.social";
const UA = "hearback/0.1 (+https://hearback.dev)";

export class BskyError extends Error {
  constructor(readonly status: number, readonly error: string, message: string, readonly resetAt?: string) {
    super(message);
  }
}

export interface Session { did: string; handle: string; accessJwt: string; refreshJwt: string; pds: string }

export function normaliseHandle(h: string): string {
  let s = h.trim().replace(/^@/, "").toLowerCase();
  if (s && !s.includes(".") && !s.startsWith("did:")) s += ".bsky.social";
  return s;
}

async function xrpc(base: string, method: "GET" | "POST", nsid: string, opts: {
  token?: string; params?: Record<string, string | string[] | number | undefined>; body?: unknown;
} = {}) {
  const u = new URL(`${base}/xrpc/${nsid}`);
  for (const [k, v] of Object.entries(opts.params ?? {})) {
    if (v === undefined) continue;
    for (const x of Array.isArray(v) ? v : [v]) u.searchParams.append(k, String(x));
  }
  const headers: Record<string, string> = { "user-agent": UA };
  if (opts.token) headers.authorization = `Bearer ${opts.token}`;
  if (opts.body !== undefined) headers["content-type"] = "application/json";
  const res = await fetch(u, { method, headers, body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined, signal: AbortSignal.timeout(20_000) });
  const text = await res.text();
  // deno-lint-ignore no-explicit-any
  let data: any = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* not json */ }
  if (!res.ok) {
    const reset = res.headers.get("ratelimit-reset");
    throw new BskyError(res.status, data?.error ?? `http_${res.status}`, `${nsid}: ${data?.message ?? res.status}`,
      reset ? new Date(Number(reset) * 1000).toISOString() : undefined);
  }
  return data;
}

/** handle or DID → {did, pds}. */
export async function resolveAccount(handleOrDid: string): Promise<{ did: string; pds: string }> {
  let did = handleOrDid;
  if (!did.startsWith("did:")) {
    try {
      did = (await xrpc(ENTRYWAY, "GET", "com.atproto.identity.resolveHandle", { params: { handle: handleOrDid } })).did;
    } catch (e) {
      if (e instanceof BskyError && e.status === 400) throw new HttpError(422, "bluesky_auth_failed", "We couldn't find that Bluesky handle.");
      throw e;
    }
  }
  const docUrl = did.startsWith("did:plc:") ? `https://plc.directory/${did}`
    : did.startsWith("did:web:") ? `https://${did.slice(8)}/.well-known/did.json` : null;
  if (!docUrl) throw new HttpError(422, "bluesky_auth_failed", "Unsupported Bluesky account type.");
  const res = await fetch(docUrl, { headers: { "user-agent": UA }, signal: AbortSignal.timeout(10_000) });
  if (!res.ok) throw new HttpError(502, "upstream_error", "Couldn't resolve the Bluesky account.");
  const doc = await res.json();
  const svc = (doc.service ?? []).find((s: { id: string }) => s.id === "#atproto_pds" || s.id.endsWith("#atproto_pds"));
  return { did, pds: (svc?.serviceEndpoint ?? ENTRYWAY).replace(/\/$/, "") };
}

export async function createSession(pds: string, identifier: string, password: string): Promise<Session> {
  try {
    const s = await xrpc(pds, "POST", "com.atproto.server.createSession", { body: { identifier, password } });
    return { did: s.did, handle: s.handle, accessJwt: s.accessJwt, refreshJwt: s.refreshJwt, pds };
  } catch (e) {
    if (e instanceof BskyError && (e.status === 401 || e.status === 400)) {
      if (e.error === "AuthFactorTokenRequired") throw new HttpError(422, "bluesky_auth_failed", "Use an app password, not your main password (your account asks for an email code).");
      throw new HttpError(422, "bluesky_auth_failed", "Handle or app password is wrong.");
    }
    if (e instanceof BskyError && e.status === 429) throw new HttpError(429, "rate_limited", "Bluesky says too many logins; try again in a few minutes.", { reset_at: e.resetAt });
    throw e;
  }
}

/** A logged-in client for one stored account; refreshes and re-logs in as needed. */
export class BskyClient {
  constructor(readonly accountId: string, private s: Session) {}
  get did() { return this.s.did; }
  get handle() { return this.s.handle; }

  static async forAccount(accountId: string): Promise<BskyClient> {
    const db = admin();
    const { data: raw } = await db.rpc("read_account_session", { p_account: accountId });
    if (raw) return new BskyClient(accountId, JSON.parse(raw));
    return new BskyClient(accountId, await BskyClient.login(accountId));
  }

  static async login(accountId: string): Promise<Session> {
    const db = admin();
    const { data: acct } = await db.from("accounts").select("handle, external_id, settings").eq("id", accountId).single();
    const { data: pw } = await db.rpc("read_account_secret", { p_account: accountId });
    if (!acct || !pw) throw new HttpError(422, "bluesky_not_connected", "Connect Bluesky again (no app password stored).");
    const pds = (acct.settings?.pds as string) ?? (await resolveAccount(acct.external_id ?? acct.handle)).pds;
    const s = await createSession(pds, acct.external_id ?? acct.handle, pw);
    await db.rpc("store_account_session", { p_account: accountId, p_session: JSON.stringify(s) });
    return s;
  }

  private async save() {
    await admin().rpc("store_account_session", { p_account: this.accountId, p_session: JSON.stringify(this.s) });
  }

  private async refresh() {
    try {
      const r = await xrpc(this.s.pds, "POST", "com.atproto.server.refreshSession", { token: this.s.refreshJwt });
      this.s = { ...this.s, accessJwt: r.accessJwt, refreshJwt: r.refreshJwt, handle: r.handle ?? this.s.handle };
    } catch {
      this.s = await BskyClient.login(this.accountId);
    }
    await this.save();
  }

  // deno-lint-ignore no-explicit-any
  async call(method: "GET" | "POST", nsid: string, opts: { params?: Record<string, any>; body?: unknown } = {}): Promise<any> {
    try {
      return await xrpc(this.s.pds, method, nsid, { ...opts, token: this.s.accessJwt });
    } catch (e) {
      if (e instanceof BskyError && (e.error === "ExpiredToken" || e.error === "InvalidToken" || e.status === 401)) {
        await this.refresh();
        return await xrpc(this.s.pds, method, nsid, { ...opts, token: this.s.accessJwt });
      }
      throw e;
    }
  }
}

export const rkeyOf = (uri: string) => uri.split("/").pop()!;
export const postUrl = (handleOrDid: string, uri: string) => `https://bsky.app/profile/${handleOrDid}/post/${rkeyOf(uri)}`;

// ------------------------------------------------------------------ facets (pure)
export interface Facet {
  index: { byteStart: number; byteEnd: number };
  features: ({ $type: "app.bsky.richtext.facet#link"; uri: string } | { $type: "app.bsky.richtext.facet#mention"; did: string })[];
}

const enc = new TextEncoder();
const byteIdx = (text: string, charIdx: number) => enc.encode(text.slice(0, charIdx)).length;

/** Links and @handles with UTF-8 byte offsets (Bluesky's rich-text rules). Mentions need a resolver. */
export function detectFacets(text: string): { links: { start: number; end: number; uri: string }[]; mentions: { start: number; end: number; handle: string }[] } {
  const links: { start: number; end: number; uri: string }[] = [];
  const mentions: { start: number; end: number; handle: string }[] = [];
  const urlRe = /(^|\s|\()((https?:\/\/)[^\s<>"')\]]+[^\s<>"')\].,;:!?])/g;
  for (const m of text.matchAll(urlRe)) {
    const start = (m.index ?? 0) + m[1].length;
    const uri = m[2];
    links.push({ start: byteIdx(text, start), end: byteIdx(text, start + uri.length), uri });
  }
  const menRe = /(^|\s|\()(@(([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?))/g;
  for (const m of text.matchAll(menRe)) {
    const start = (m.index ?? 0) + m[1].length;
    mentions.push({ start: byteIdx(text, start), end: byteIdx(text, start + m[2].length), handle: m[3].toLowerCase() });
  }
  return { links, mentions };
}

export async function buildFacets(text: string, resolve: (handle: string) => Promise<string | null>): Promise<Facet[]> {
  const { links, mentions } = detectFacets(text);
  const out: Facet[] = links.map((l) => ({ index: { byteStart: l.start, byteEnd: l.end }, features: [{ $type: "app.bsky.richtext.facet#link", uri: l.uri }] }));
  for (const m of mentions) {
    const did = await resolve(m.handle).catch(() => null);
    if (did) out.push({ index: { byteStart: m.start, byteEnd: m.end }, features: [{ $type: "app.bsky.richtext.facet#mention", did }] });
  }
  return out.sort((a, b) => a.index.byteStart - b.index.byteStart);
}

export async function resolveHandleDid(handle: string): Promise<string | null> {
  try {
    return (await xrpc(ENTRYWAY, "GET", "com.atproto.identity.resolveHandle", { params: { handle } })).did ?? null;
  } catch {
    return null;
  }
}
