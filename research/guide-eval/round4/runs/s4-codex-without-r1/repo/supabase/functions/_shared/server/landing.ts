// Fetch a founder's landing page safely and turn it into text: http(s) only,
// every hop's address checked against private/loopback ranges (SSRF), at most
// 5 redirects, 8 s per hop, 1.5 MB cap. Then the model reads it.

import type { Provider } from "../draft/mod.ts";
import { HttpError } from "./http.ts";

const MAX_BYTES = 1_500_000;
const UA = "Mozilla/5.0 (compatible; HearbackBot/0.1; +https://hearback.dev)";

export class LandingError extends Error {
  constructor(readonly reason: string, readonly status: number | null, message: string) {
    super(message);
  }
}

/** Pure. True for loopback, private, link-local, CGNAT, multicast, reserved and unspecified addresses. */
export function isPrivateIp(ip: string): boolean {
  const v4 = ip.match(/^(\d+)\.(\d+)\.(\d+)\.(\d+)$/);
  if (v4) {
    const [a, b] = [Number(v4[1]), Number(v4[2])];
    return a === 0 || a === 10 || a === 127 || (a === 100 && b >= 64 && b <= 127) || (a === 169 && b === 254) ||
      (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || (a === 192 && b === 0) || (a === 198 && (b === 18 || b === 19)) ||
      a >= 224;
  }
  const s = ip.toLowerCase().replace(/^\[|\]$/g, "");
  if (s === "::" || s === "::1") return true;
  const mapped = s.match(/^::ffff:(\d+\.\d+\.\d+\.\d+)$/);
  if (mapped) return isPrivateIp(mapped[1]);
  return /^(fc|fd|fe8|fe9|fea|feb|ff)/.test(s) || s.startsWith("64:ff9b:") || s.startsWith("2001:db8");
}

/** Pure. "patchwork.dev" → "https://patchwork.dev/"; null when it can't be a public web address. */
export function normaliseUrl(input: string): string | null {
  let s = input.trim();
  if (!s) return null;
  if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(s)) s = `https://${s}`;
  try {
    const u = new URL(s);
    if (u.protocol !== "https:" && u.protocol !== "http:") return null;
    if (!u.hostname.includes(".") || u.username || u.password) return null;
    if (u.port && u.port !== "80" && u.port !== "443") return null;
    return u.toString();
  } catch {
    return null;
  }
}

async function assertPublicHost(host: string) {
  const h = host.replace(/^\[|\]$/g, "");
  if (/^[\d.]+$/.test(h) || h.includes(":")) {
    if (isPrivateIp(h)) throw new LandingError("blocked_address", null, "That address is not public.");
    return;
  }
  if (h === "localhost" || h.endsWith(".localhost") || h.endsWith(".local") || h.endsWith(".internal")) {
    throw new LandingError("blocked_address", null, "That address is not public.");
  }
  const addrs: string[] = [];
  for (const t of ["A", "AAAA"] as const) {
    try { addrs.push(...await Deno.resolveDns(h, t)); } catch { /* none of this type */ }
  }
  if (!addrs.length) throw new LandingError("dns", null, "That domain doesn't resolve.");
  if (addrs.some(isPrivateIp)) throw new LandingError("blocked_address", null, "That address is not public.");
}

export async function safeFetch(url: string): Promise<{ status: number; finalUrl: string; html: string; contentType: string }> {
  let current = url;
  for (let hop = 0; hop <= 5; hop++) {
    const u = new URL(current);
    if (u.protocol !== "https:" && u.protocol !== "http:") throw new LandingError("blocked_address", null, "Only web addresses.");
    await assertPublicHost(u.hostname);
    let res: Response;
    try {
      res = await fetch(current, {
        redirect: "manual", signal: AbortSignal.timeout(8000),
        headers: { "user-agent": UA, accept: "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5" },
      });
    } catch (e) {
      const m = (e as Error).message ?? "";
      throw new LandingError(/timed out|abort/i.test(m) ? "timeout" : "unreachable", null, "The site didn't answer.");
    }
    if (res.status >= 300 && res.status < 400 && res.headers.get("location")) {
      await res.body?.cancel();
      current = new URL(res.headers.get("location")!, current).toString();
      continue;
    }
    if (!res.ok) {
      await res.body?.cancel();
      throw new LandingError(`http_${res.status}`, res.status, `Error: ${res.status}`);
    }
    const ct = res.headers.get("content-type") ?? "";
    if (ct && !/html|xml|text\/plain/i.test(ct)) {
      await res.body?.cancel();
      throw new LandingError("not_html", res.status, "That address is not a web page.");
    }
    const reader = res.body!.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > MAX_BYTES) { await reader.cancel(); break; }
      chunks.push(value);
    }
    const buf = new Uint8Array(chunks.reduce((n, c) => n + c.length, 0));
    let off = 0;
    for (const c of chunks) { buf.set(c, off); off += c.length; }
    return { status: res.status, finalUrl: current, html: new TextDecoder().decode(buf), contentType: ct };
  }
  throw new LandingError("too_many_redirects", null, "Too many redirects.");
}

const ent = (s: string) => s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"')
  .replace(/&#39;|&apos;/g, "'").replace(/&nbsp;/g, " ").replace(/&#(\d+);/g, (_m, n) => String.fromCodePoint(Number(n)))
  .replace(/&#x([0-9a-f]+);/gi, (_m, n) => String.fromCodePoint(parseInt(n, 16)));

/** Pure. Page HTML → title, description, favicon, readable text (≤12k chars). */
export function extractPage(html: string, baseUrl: string) {
  const meta = (name: string) => {
    const re = new RegExp(`<meta[^>]+(?:name|property)=["']${name}["'][^>]*>`, "i");
    const tag = html.match(re)?.[0];
    return tag ? ent(tag.match(/content=["']([^"']*)["']/i)?.[1] ?? "").trim() : "";
  };
  const title = ent(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1] ?? "").replace(/\s+/g, " ").trim() || meta("og:title");
  const description = meta("description") || meta("og:description");
  const iconHref = html.match(/<link[^>]+rel=["'][^"']*icon[^"']*["'][^>]*>/i)?.[0]?.match(/href=["']([^"']+)["']/i)?.[1];
  let favicon: string | null = null;
  try { favicon = new URL(iconHref ?? "/favicon.ico", baseUrl).toString(); } catch { /* ignore */ }
  const body = html
    .replace(/<(script|style|noscript|svg|template|iframe)[\s\S]*?<\/\1>/gi, " ")
    .replace(/<!--[\s\S]*?-->/g, " ")
    .replace(/<\/(p|div|section|h[1-6]|li|tr|br|header|footer|article)>/gi, "\n")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<[^>]+>/g, " ");
  const text = ent(body).split("\n").map((l) => l.replace(/\s+/g, " ").trim()).filter((l) => l.length > 1)
    .filter((l, i, a) => a.indexOf(l) === i).join("\n").slice(0, 12_000);
  return { title, description, favicon, text };
}

export interface LandingRead {
  name: string; one_liner: string; audience: string[]; topics: string[]; competitors: string[]; aims: string;
}

/** Pure. Model JSON → a clean LandingRead (lists trimmed, capped, deduped). */
export function parseLandingJson(raw: string, fallbackName: string): LandingRead {
  const t = raw.trim().replace(/^```(?:json)?\s*|\s*```$/g, "");
  // deno-lint-ignore no-explicit-any
  let j: any;
  try { j = JSON.parse(t); } catch { j = JSON.parse(t.slice(t.indexOf("{"), t.lastIndexOf("}") + 1)); }
  const list = (v: unknown, max: number) => Array.isArray(v)
    ? [...new Set(v.map((x) => String(x).trim()).filter((x) => x && x.length <= 80))].slice(0, max) : [];
  return {
    name: String(j.name ?? "").trim().slice(0, 80) || fallbackName,
    one_liner: String(j.one_liner ?? "").trim().slice(0, 200),
    audience: list(j.audience, 5),
    topics: list(j.topics, 10),
    competitors: list(j.competitors, 6),
    aims: String(j.aims ?? "").trim().slice(0, 300),
  };
}

export async function readWithModel(llm: Provider, src: { url?: string; title?: string; description?: string; text: string }, fallbackName: string): Promise<LandingRead> {
  const prompt = [
    src.url ? `URL: ${src.url}` : "",
    src.title ? `Title: ${src.title}` : "",
    src.description ? `Meta description: ${src.description}` : "",
    `Text:\n${src.text.slice(0, 10_000)}`,
    "",
    `From this product's landing page (or the founder's own description), return JSON:
{"name": product name,
 "one_liner": what it does, max 15 words, plain words, no hype,
 "audience": 2-4 short labels for who it's for (e.g. "Indie developers"),
 "topics": 4-8 short phrases or hashtags people use when they POST about this problem (what to listen for on Bluesky and dev.to), lowercase,
 "competitors": named similar products mentioned or obvious (0-5; [] if unsure),
 "aims": one sentence: what the founder probably wants from conversations now (e.g. "find first users among indie developers")}
Use only what the text supports. Return only JSON.`,
  ].filter(Boolean).join("\n");
  const out = await llm.generate({ system: "You read product landing pages and return compact JSON.", prompt, temperature: 0.2, json: true, max_output_tokens: 600 });
  try {
    return parseLandingJson(out.text, fallbackName);
  } catch {
    throw new HttpError(502, "upstream_error", "The model's answer was unreadable; try again.");
  }
}
