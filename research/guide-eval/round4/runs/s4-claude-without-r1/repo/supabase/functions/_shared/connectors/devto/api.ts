// dev.to (Forem) public API, no key (eval/DEVTO-API-NOTES.md): ≤1 req/s,
// 30 req/min, Retry-After on 429, no rate-limit headers. Comments on the
// founder's own articles come from GET /api/comments?a_id=ID (nested tree).
// The connector's rate rules (DEVTO_RATE) drive this client.

const BASE = "https://dev.to/api";
const UA = "hearback/0.1 (+https://hearback.dev)";

export const DEVTO_RATE = { minIntervalMs: 1100, maxRequestsPerRun: 25, on429: "retry_after" as const, maxRetryAfterS: 40 };

export class DevtoPublic {
  #last = 0;
  requests = 0;
  constructor(private maxRequests = DEVTO_RATE.maxRequestsPerRun, private minIntervalMs = DEVTO_RATE.minIntervalMs) {}

  async get<T>(path: string): Promise<T | null> {
    for (let attempt = 0; attempt < 3; attempt++) {
      if (this.requests >= this.maxRequests) throw new Error(`dev.to request budget for this run reached (${this.maxRequests})`);
      const wait = this.#last + this.minIntervalMs - Date.now();
      if (wait > 0) await new Promise((r) => setTimeout(r, wait));
      this.#last = Date.now();
      this.requests++;
      const res = await fetch(`${BASE}${path}`, {
        headers: { "user-agent": UA, accept: "application/vnd.forem.api-v1+json" },
        signal: AbortSignal.timeout(15_000),
      });
      if (res.status === 404) { await res.body?.cancel(); return null; }
      if (res.status === 429) {
        await res.body?.cancel();
        const ra = Number(res.headers.get("retry-after") ?? 10);
        if (ra > DEVTO_RATE.maxRetryAfterS) throw new Error(`dev.to 429, Retry-After ${ra}s`);
        await new Promise((r) => setTimeout(r, (ra + 1) * 1000));
        continue;
      }
      if (!res.ok) { await res.body?.cancel(); throw new Error(`dev.to ${res.status} on ${path.split("?")[0]}`); }
      return await res.json() as T;
    }
    throw new Error("dev.to: rate limited, gave up");
  }
}

export interface DevtoArticle {
  id: number; title: string; url: string; description?: string; comments_count: number;
  published_at: string; tag_list?: string[] | string; user?: { username: string; name?: string }; body_markdown?: string;
  positive_reactions_count?: number;
}

export interface DevtoCommentNode {
  id_code: string;
  created_at: string;
  body_html: string;
  /** Empty ({}) for a comment the article's author hid, and for deleted ones. */
  user?: { username?: string; name?: string; profile_image_90?: string; profile_image?: string };
  children?: DevtoCommentNode[];
}
