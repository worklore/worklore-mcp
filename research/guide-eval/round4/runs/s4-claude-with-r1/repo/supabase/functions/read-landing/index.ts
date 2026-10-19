// POST /functions/v1/read-landing  {project_id?, url | description, check_only?}
// Onboarding: read the landing page (or the founder's description), extract
// name / one-liner / audience / topics / competitors, store them on the project
// (creating it when there's no project_id). docs/API.md › read-landing

import { admin, caller, requireMember } from "../_shared/server/ctx.ts";
import { bad, HttpError, serve, str, uuid } from "../_shared/server/http.ts";
import { extractPage, LandingError, normaliseUrl, readWithModel, safeFetch } from "../_shared/server/landing.ts";
import { utilityProvider } from "../_shared/server/models.ts";

/** The founder's existing project for this URL (member of, same url key), if any. */
async function existingProject(founderId: string, ...urls: (string | null)[]): Promise<string | null> {
  for (const u of urls) {
    if (!u) continue;
    const { data, error } = await admin().rpc("project_for_url", { p_founder: founderId, p_url: u });
    if (error) throw error;
    if (data) return data as string;
  }
  return null;
}

serve(async (req, body) => {
  const c = await caller(req);
  let projectId = uuid(body.project_id, "project_id", false);
  // The service role (seeding) may only fill an existing project.
  if (c.kind === "service" && !projectId) throw bad("project_id is required for the service role");
  const rawUrl = str(body.url, "url", { max: 2000 });
  const description = str(body.description, "description", { max: 4000 })?.trim();
  if (!rawUrl && !description) throw bad("Give a url or a description.");
  const url = rawUrl ? normaliseUrl(rawUrl) : null;
  if (rawUrl && !url) throw bad("That doesn't look like a web address.", { reason: "invalid_url" });
  if (!rawUrl && description!.length < 20) throw bad("Describe it in at least 20 characters.");

  if (body.check_only === true) {
    if (!url) throw bad("check_only needs a url");
    try {
      const page = await safeFetch(url);
      const ex = extractPage(page.html, page.finalUrl);
      return { reachable: true, status: page.status, final_url: page.finalUrl, title: ex.title || null, favicon: ex.favicon };
    } catch (e) {
      if (e instanceof LandingError) return { reachable: false, status: e.status, reason: e.reason, final_url: null, title: null, favicon: null };
      throw e;
    }
  }
  // Idempotent create: a founder who already has a project for this URL gets
  // that project back (filled again), never a second one.
  let existing = false;
  if (!projectId && url && c.kind === "user") {
    projectId = (await existingProject(c.userId, url)) ?? undefined;
    existing = !!projectId;
  }
  if (projectId) await requireMember(c, projectId);

  let src: { url?: string; title?: string; description?: string; text: string };
  let finalUrl: string | null = null;
  const host = url ? new URL(url).hostname.replace(/^www\./, "") : null;
  if (url) {
    try {
      const page = await safeFetch(url);
      const ex = extractPage(page.html, page.finalUrl);
      finalUrl = page.finalUrl;
      if ((ex.text + ex.description).replace(/\s/g, "").length < 80) throw new LandingError("too_little_text", page.status, "The page has almost no text (maybe it needs JavaScript).");
      src = { url: page.finalUrl, title: ex.title, description: ex.description, text: [description, ex.text].filter(Boolean).join("\n\n") };
    } catch (e) {
      if (e instanceof LandingError) {
        throw new HttpError(422, "landing_unreachable", `We couldn't open ${host}`, { status: e.status, reason: e.reason, url });
      }
      throw e;
    }
  } else {
    src = { text: description! };
  }

  const read = await readWithModel(utilityProvider(undefined, "landing"), src, host ?? "My project");
  const fields = {
    one_liner: read.one_liner || null, audience: read.audience, topics: read.topics, competitors: read.competitors,
    aims: read.aims || null, landing_read_at: new Date().toISOString(),
    landing: { ...read, source: url ? "url" : "description", final_url: finalUrl, title: src.title ?? null },
    ...(url ? { url: finalUrl ?? url } : {}), ...(description ? { description } : {}),
  };
  const db = admin();
  let project;
  if (projectId) {
    const { data: cur } = await db.from("projects").select("name").eq("id", projectId).single();
    const { data, error } = await db.from("projects").update({ ...fields, ...(cur?.name ? {} : { name: read.name }) })
      .eq("id", projectId).select("*").single();
    if (error) throw error;
    project = data;
  } else {
    if (c.kind !== "user") throw bad("project_id is required");
    // The page may have redirected to an address an existing project already has.
    const again = await existingProject(c.userId, finalUrl, url);
    existing = !!again;
    const { data, error } = again
      ? await db.from("projects").update(fields).eq("id", again).select("*").single()
      : await db.from("projects").insert({ ...fields, name: read.name, created_by: c.userId }).select("*").single();
    if (error?.code === "23505") {
      // A parallel call created it meanwhile (unique creator + url_key): use that one.
      const winner = await existingProject(c.userId, finalUrl, url);
      if (!winner) throw error;
      existing = true;
      const r = await db.from("projects").update(fields).eq("id", winner).select("*").single();
      if (r.error) throw r.error;
      project = r.data;
    } else {
      if (error) throw error;
      project = data;
    }
  }
  const { knowledge_sources: _k, ...pub } = project;
  // existing: true when this returned a project she already had (no new one was created).
  return { project: pub, existing, read: { ...read, source: url ? "url" : "description", final_url: finalUrl, title: src.title ?? null } };
});
