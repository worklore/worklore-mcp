// The product's own site as knowledge: the landing page plus pages it links
// to on the same site (capped). Platform-free; uses the landing reader's SSRF-
// safe fetch. A page is dated by its article:published_time / modified_time
// meta when it has one, else by when Hearback first saw that exact text (kept
// in the source's state), so an unchanged page keeps its date and its hash.

import { extractPage, safeFetch } from "../../server/landing.ts";
import type { SourceBatch, SourceDocument } from "../types.ts";

export const SITE_PAGE_CAP = 12;

const SKIP_EXT = /\.(xml|rss|atom|json|txt|pdf|png|jpe?g|gif|svg|webp|ico|css|js|mjs|zip|gz|mp4|mp3|woff2?)$/i;
const SKIP_PATH = /^\/(login|signin|sign-in|signup|sign-up|register|logout|auth|account|cart|checkout|admin|api|cdn-cgi|wp-admin)(\/|$)/i;

const host = (u: URL) => u.hostname.toLowerCase().replace(/^www\./, "");

/** Pure. Same-site page links in `html`, shallow paths first, then in page order; at most `cap`. */
export function sameSiteLinks(html: string, baseUrl: string, cap = SITE_PAGE_CAP - 1): string[] {
  const base = new URL(baseUrl);
  const seen = new Set<string>([canonical(base)]);
  const out: { url: string; depth: number; i: number }[] = [];
  let i = 0;
  for (const m of html.matchAll(/<a\b[^>]*\bhref\s*=\s*["']([^"'#][^"']*)["']/gi)) {
    let u: URL;
    try { u = new URL(m[1].replace(/&amp;/g, "&"), base); } catch { continue; }
    if (!/^https?:$/.test(u.protocol) || host(u) !== host(base)) continue;
    if (SKIP_EXT.test(u.pathname) || SKIP_PATH.test(u.pathname)) continue;
    u.hash = ""; u.search = "";
    const key = canonical(u);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ url: u.toString(), depth: u.pathname.split("/").filter(Boolean).length, i: i++ });
  }
  return out.sort((a, b) => a.depth - b.depth || a.i - b.i).slice(0, cap).map((x) => x.url);
}

function canonical(u: URL) {
  return `${host(u)}${u.pathname.replace(/\/+$/, "").replace(/\/index\.html?$/, "") || "/"}`;
}

/** Pure. The page's own date: article:*_time / og:updated_time / date meta, else JSON-LD dateModified / datePublished. */
export function metaDate(html: string): string | null {
  const ok = (v: string | undefined) => v && !isNaN(new Date(v).getTime()) ? (v.length <= 10 ? v : new Date(v).toISOString()) : null;
  for (const name of ["article:modified_time", "article:published_time", "og:updated_time", "date"]) {
    const tag = html.match(new RegExp(`<meta[^>]+(?:name|property)=["']${name}["'][^>]*>`, "i"))?.[0];
    const v = ok(tag?.match(/content=["']([^"']+)["']/i)?.[1]);
    if (v) return v;
  }
  for (const key of ["dateModified", "datePublished"]) {
    const v = ok(html.match(new RegExp(`"${key}"\\s*:\\s*"([^"]+)"`))?.[1]);
    if (v) return v;
  }
  return null;
}

async function hash(s: string) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(h)].slice(0, 12).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export interface SiteFetch { (url: string): Promise<{ finalUrl: string; html: string }> }

/** Reads the landing page and its same-site links. `state.pages` = {url: {sha, seen}}. */
export async function readSite(url: string, state: Record<string, unknown>, deadline: number, fetchPage: SiteFetch = safeFetch): Promise<SourceBatch> {
  const prev = (state.pages ?? {}) as Record<string, { sha: string; seen: string }>;
  const pages: Record<string, { sha: string; seen: string }> = {};
  const documents: SourceDocument[] = [];
  const errors: string[] = [];
  const now = new Date().toISOString();
  const read = async (u: string) => {
    const { finalUrl, html } = await fetchPage(u);
    const p = extractPage(html, finalUrl);
    if (p.text.length < 200) return { html, doc: null };
    const sha = await hash(p.text);
    const seen = prev[u]?.sha === sha ? prev[u].seen : now;
    pages[u] = { sha, seen };
    const doc: SourceDocument = {
      kind: "page", title: p.title || new URL(finalUrl).pathname, url: u, published_at: metaDate(html) ?? seen,
      markdown: [p.description, p.text].filter(Boolean).join("\n\n"), label: "quotable",
    };
    return { html, doc };
  };
  let landing;
  try {
    landing = await read(url);
  } catch (e) {
    return { documents: [], status: "error", message: `Couldn't read ${url}: ${(e as Error).message}`, state };
  }
  if (landing.doc) documents.push(landing.doc);
  for (const link of sameSiteLinks(landing.html, url)) {
    if (Date.now() > deadline) break;
    try {
      const r = await read(link);
      if (r.doc) documents.push(r.doc);
    } catch (e) { errors.push(`${new URL(link).pathname}: ${(e as Error).message}`); }
  }
  return {
    documents, state: { pages: { ...prev, ...pages } }, status: documents.length ? "ok" : "empty",
    message: errors.length ? `${errors.length} page(s) unreadable` : null, stats: { pages: documents.length },
  };
}
