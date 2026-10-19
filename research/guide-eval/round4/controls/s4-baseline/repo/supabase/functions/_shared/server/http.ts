// HTTP plumbing shared by every function: CORS (the web build calls from
// app.hearback.dev and localhost), JSON responses, the error shape of
// docs/API.md ({error: {code, message, details}}), and a handler wrapper.

import { withUsage } from "./usage.ts";

export const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "authorization, x-client-info, apikey, content-type",
  "access-control-allow-methods": "POST, OPTIONS",
};

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { ...CORS, "content-type": "application/json" } });
}

export class HttpError extends Error {
  constructor(readonly status: number, readonly code: string, message: string, readonly details?: Record<string, unknown>) {
    super(message);
  }
}

export const bad = (message: string, details?: Record<string, unknown>) => new HttpError(400, "bad_request", message, details);

export function errorResponse(e: unknown): Response {
  if (e instanceof HttpError) {
    return json({ error: { code: e.code, message: e.message, ...(e.details ? { details: e.details } : {}) } }, e.status);
  }
  // deno-lint-ignore no-explicit-any
  const err = e as any;
  if (err?.name === "ProviderError" || err?.constructor?.name === "ProviderError") {
    const s = err.status === 429 ? 429 : 502;
    return json({ error: { code: s === 429 ? "rate_limited" : "upstream_error", message: s === 429 ? "The model is busy or out of quota; try again later." : "The model failed; try again." } }, s);
  }
  console.error("internal error:", err?.message ?? String(e));
  return json({ error: { code: "internal", message: "Something went wrong on our side." } }, 500);
}

/** Pure: the function's name from its URL ("/functions/v1/ask-code" or "/ask-code" → "ask-code"). */
export function functionName(url: string): string | undefined {
  const parts = new URL(url).pathname.split("/").filter(Boolean);
  return (parts[0] === "functions" && parts[1] === "v1" ? parts[2] : parts[0]) ?? undefined;
}

/**
 * Wraps a POST JSON handler: CORS preflight, method check, body parse,
 * errors. Model calls made while handling are logged under the function's
 * name (usage.ts).
 */
export function serve(handler: (req: Request, body: Record<string, unknown>) => Promise<unknown>) {
  Deno.serve((req) => withUsage({ fn: functionName(req.url) }, () => handle(req, handler)));
}

async function handle(req: Request, handler: (req: Request, body: Record<string, unknown>) => Promise<unknown>): Promise<Response> {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: { code: "bad_request", message: "POST only" } }, 405);
  try {
    let body: Record<string, unknown> = {};
    const text = await req.text();
    if (text.trim()) {
      try { body = JSON.parse(text); } catch { throw bad("Body must be JSON"); }
      if (!body || typeof body !== "object" || Array.isArray(body)) throw bad("Body must be a JSON object");
    }
    const out = await handler(req, body);
    return out instanceof Response ? out : json(out);
  } catch (e) {
    return errorResponse(e);
  }
}

export function str(v: unknown, name: string, opts: { required?: boolean; max?: number } = {}): string | undefined {
  if (v === undefined || v === null || v === "") {
    if (opts.required) throw bad(`${name} is required`);
    return undefined;
  }
  if (typeof v !== "string") throw bad(`${name} must be a string`);
  if (opts.max && v.length > opts.max) throw bad(`${name} is too long (max ${opts.max})`);
  return v;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function uuid(v: unknown, name: string, required = true): string | undefined {
  const s = str(v, name, { required });
  if (s !== undefined && !UUID.test(s)) throw bad(`${name} must be a uuid`);
  return s;
}
