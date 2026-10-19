// Who is calling and what they may touch. JWT verification is on for every
// function (the gateway rejects bad tokens); here we tell a founder's session
// from the service role (pg_cron), and check project membership.

import { createClient, SupabaseClient } from "npm:@supabase/supabase-js@2";
import { HttpError } from "./http.ts";
import { tagUsage } from "./usage.ts";

export type Caller =
  | { kind: "user"; userId: string; email?: string; jwt: string; db: SupabaseClient }
  | { kind: "service" };

let _admin: SupabaseClient | null = null;
export function admin(): SupabaseClient {
  return _admin ??= createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}

/** Payload of a JWT (already verified by the gateway); never trusted for anything but routing. */
export function jwtPayload(jwt: string): Record<string, unknown> {
  try {
    const p = jwt.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(p + "=".repeat((4 - p.length % 4) % 4)));
  } catch {
    return {};
  }
}

export async function caller(req: Request): Promise<Caller> {
  const jwt = req.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  if (!jwt) throw new HttpError(401, "unauthorized", "Sign in first.");
  const p = jwtPayload(jwt);
  if (p.role === "service_role") {
    // verify_jwt is on for every function: the gateway already checked the
    // signature with the project's JWT secret, so the role claim is genuine.
    return { kind: "service" };
  }
  const { data, error } = await admin().auth.getUser(jwt);
  if (error || !data.user) throw new HttpError(401, "unauthorized", "Your session expired. Sign in again.");
  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_ANON_KEY")!, {
    global: { headers: { Authorization: `Bearer ${jwt}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  tagUsage({ founder_id: data.user.id });
  return { kind: "user", userId: data.user.id, email: data.user.email, jwt, db };
}

export async function requireUser(req: Request) {
  const c = await caller(req);
  if (c.kind !== "user") throw new HttpError(403, "forbidden", "This needs a signed-in founder.");
  return c;
}

/** Throws 403 unless the caller is a member (service role passes). */
export async function requireMember(c: Caller, projectId: string): Promise<void> {
  tagUsage({ project_id: projectId });
  if (c.kind === "service") return;
  const { data, error } = await admin().from("project_members").select("role")
    .eq("project_id", projectId).eq("founder_id", c.userId).maybeSingle();
  if (error) throw error;
  if (!data) throw new HttpError(403, "forbidden", "You're not a member of this project.");
}

/** The founder who answers for a project when no one is signed in (cron): its creator, else an owner. */
export async function projectFounder(projectId: string): Promise<string | null> {
  const db = admin();
  const { data: p } = await db.from("projects").select("created_by").eq("id", projectId).single();
  if (p?.created_by) return p.created_by;
  const { data: m } = await db.from("project_members").select("founder_id").eq("project_id", projectId)
    .order("role", { ascending: true }).limit(1).maybeSingle();
  return m?.founder_id ?? null;
}

/** Runs work after the response when the runtime allows it (EdgeRuntime.waitUntil). */
export function background(p: Promise<unknown>) {
  const guarded = p.catch((e) => console.error("background:", (e as Error).message));
  // deno-lint-ignore no-explicit-any
  const rt = (globalThis as any).EdgeRuntime;
  if (rt?.waitUntil) rt.waitUntil(guarded);
}

export const env = (k: string) => Deno.env.get(k);
