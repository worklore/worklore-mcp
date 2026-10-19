// POST /functions/v1/discover  {project_id, limit?: 5}
// "First conversations": recent posts on Bluesky (search through her session,
// if connected) and dev.to articles under her topics → relevance by the
// decider (Jev) → the top few stored as items with origin='discover'.
// Capped: ≤3 topics per network, ≤12 decisions, 1 model call for the "why" lines.
// docs/API.md › discover

import { ArticleInput, decideArticle } from "../_shared/draft/mod.ts";
import "../_shared/connectors/mod.ts";
import { BskyClient, postUrl } from "../_shared/connectors/bluesky/client.ts";
import { DevtoArticle, DevtoPublic } from "../_shared/connectors/devto/api.ts";
import { connector } from "../_shared/core/registry.ts";
import { insertItem, upsertPerson } from "../_shared/core/store.ts";
import { discoveryTriage } from "../_shared/core/triage_run.ts";
import { admin, caller, projectFounder, requireMember } from "../_shared/server/ctx.ts";
import { bad, serve, uuid } from "../_shared/server/http.ts";
import { decider, utilityProvider } from "../_shared/server/models.ts";
import { topicScore } from "../_shared/server/text.ts";

interface Candidate {
  platform: "bluesky" | "devto";
  external_id: string;
  url: string;
  title: string;
  text: string;
  author: { handle: string; did?: string; name?: string | null; avatar?: string | null; profile_url: string };
  posted_at: string;
  tags: string[];
  engagement: number;
  query: string;
  ref?: { uri: string; cid: string };
  article_id?: number;
}

const tagOf = (topic: string) => topic.toLowerCase().replace(/[^a-z0-9]/g, "");

serve(async (req, body) => {
  const c = await caller(req);
  const projectId = uuid(body.project_id, "project_id")!;
  await requireMember(c, projectId);
  const limit = Math.min(10, Math.max(1, Number(body.limit ?? 5)));
  const db = admin();
  const { data: project } = await db.from("projects").select("name, one_liner, audience, aims, topics").eq("id", projectId).single();
  if (!project) throw bad("No such project");
  const topics: string[] = (project.topics ?? []).slice(0, 6);
  if (!topics.length) throw bad("The project has no topics yet (read the landing page first).");
  const founderId = c.kind === "user" ? c.userId : await projectFounder(projectId);
  const { data: founder } = await db.from("founders").select("display_name").eq("id", founderId ?? "").maybeSingle();
  const { data: accounts } = await db.from("accounts").select("id, platform, handle, secret_id").eq("project_id", projectId).eq("active", true);
  const own = new Set((accounts ?? []).map((a) => a.handle.toLowerCase()));
  const since = new Date(Date.now() - 7 * 86400_000).toISOString();
  const cands: Candidate[] = [];
  const errors: string[] = [];

  // Each network is searched only while its connector is on (Bluesky is off for now).
  const bsAcct = connector("bluesky")?.enabled() ? (accounts ?? []).find((a) => a.platform === "bluesky" && a.secret_id) : undefined;
  if (bsAcct) {
    try {
      const client = await BskyClient.forAccount(bsAcct.id);
      for (const q of topics.slice(0, 3)) {
        const r = await client.call("GET", "app.bsky.feed.searchPosts", { params: { q, limit: 25, sort: "latest", since } });
        for (const p of r.posts ?? []) {
          if (p.author?.did === client.did || p.record?.reply) continue; // skip her own posts and replies deep in threads
          cands.push({
            platform: "bluesky", external_id: p.uri, url: postUrl(p.author.handle, p.uri), title: "", text: p.record?.text ?? "",
            author: { handle: p.author.handle, did: p.author.did, name: p.author.displayName, avatar: p.author.avatar, profile_url: `https://bsky.app/profile/${p.author.handle}` },
            posted_at: p.record?.createdAt ?? p.indexedAt, tags: [], engagement: (p.likeCount ?? 0) + 2 * (p.replyCount ?? 0), query: q,
            ref: { uri: p.uri, cid: p.cid },
          });
        }
      }
    } catch (e) { errors.push(`bluesky: ${(e as Error).message.slice(0, 160)}`); }
  }

  try {
    const api = new DevtoPublic(6);
    const tags = [...new Set(topics.map(tagOf).filter((t) => t.length >= 2 && t.length <= 30))].slice(0, 3);
    for (const tag of tags) {
      const list = await api.get<DevtoArticle[]>(`/articles?tag=${tag}&per_page=30&top=7`) ?? [];
      for (const a of list) {
        if (!a.user?.username || own.has(a.user.username.toLowerCase())) continue;
        cands.push({
          platform: "devto", external_id: `article:${a.id}`, url: a.url, title: a.title, text: a.description ?? "",
          author: { handle: a.user.username, name: a.user.name, profile_url: `https://dev.to/${a.user.username}` },
          posted_at: a.published_at, tags: Array.isArray(a.tag_list) ? a.tag_list : String(a.tag_list ?? "").split(/,\s*/),
          engagement: (a.positive_reactions_count ?? 0) + 2 * (a.comments_count ?? 0), query: tag, article_id: a.id,
        });
      }
    }
  } catch (e) { errors.push(`devto: ${(e as Error).message.slice(0, 160)}`); }

  const uniq = [...new Map(cands.map((x) => [x.external_id, x])).values()];
  const { data: known } = await db.from("items").select("external_id").eq("project_id", projectId)
    .in("external_id", uniq.map((x) => x.external_id).slice(0, 300));
  const knownSet = new Set((known ?? []).map((k) => k.external_id));
  const scored = uniq.filter((x) => !knownSet.has(x.external_id))
    .map((x) => ({ x, s: topicScore(`${x.title} ${x.text} ${x.tags.join(" ")}`, topics) }));
  const matched = scored.filter((y) => y.s > 0 || y.x.platform === "bluesky");
  const shortlist = matched.sort((a, b) => b.s - a.s || b.x.engagement - a.x.engagement).slice(0, 12);

  const dec = decider();
  const pin: ArticleInput["project"] = {
    name: project.name, one_liner: project.one_liner, audience: (project.audience ?? []).join("; "), aims: project.aims,
    founder_name: founder?.display_name ?? null,
  };
  const decided = [];
  for (const { x } of shortlist) {
    try {
      const d = await decideArticle({ project: pin, article: { title: x.title || x.text.slice(0, 80), url: x.url, author: x.author.handle, tags: x.tags, text: x.text, published_at: x.posted_at } }, dec);
      if (d.relevant && d.action !== "leave") decided.push({ x, d });
    } catch (e) { errors.push(`decide: ${(e as Error).message.slice(0, 120)}`); }
  }
  const top = decided.sort((a, b) => b.d.p_relevant - a.d.p_relevant).slice(0, limit);

  // One short "why" per result, in one call; a missing line falls back to the topic.
  let whys: string[] = [];
  if (top.length) {
    try {
      const out = await utilityProvider(undefined, "discover_why").generate({
        system: "You explain in one short line why a post is worth a founder's time. Return only JSON.",
        prompt: `Founder of ${project.name}: ${project.one_liner ?? ""}\n\n${top.map((t, i) => `${i + 1}. ${t.x.title ? `"${t.x.title}" ` : ""}${t.x.text.slice(0, 400)}`).join("\n\n")}\n\nFor each post, one line (max 14 words) on why she should join this conversation. Return {"why": ["…", …]} in the same order.`,
        temperature: 0.3, json: true, max_output_tokens: 400,
      });
      whys = JSON.parse(out.text.replace(/^```(?:json)?\s*|\s*```$/g, "")).why ?? [];
    } catch (e) { errors.push(`why: ${(e as Error).message.slice(0, 120)}`); }
  }

  const results = [];
  for (const [i, { x, d }] of top.entries()) {
    const personId = await upsertPerson(projectId, x.platform, {
      handle: x.author.handle, external_id: x.author.did ?? null, display_name: x.author.name ?? null, avatar_url: x.author.avatar ?? null,
      profile_url: x.author.profile_url,
    });
    const discovery = { why: (whys[i] ?? "").trim() || `About ${x.query}`, p_relevant: d.p_relevant, action: d.action, query: x.query, title: x.title || null, source: x.platform, decider: d.decider };
    const r = await insertItem({
      project_id: projectId, account_id: x.platform === "bluesky" ? bsAcct?.id ?? null : (accounts ?? []).find((a) => a.platform === "devto")?.id ?? null,
      person_id: personId, platform: x.platform, kind: "post", external_id: x.external_id, url: x.url,
      text: x.title ? `${x.title}\n\n${x.text}` : x.text, posted_at: x.posted_at,
      root_ref: x.ref ?? { article_id: x.article_id }, parent_ref: x.ref ?? { article_id: x.article_id },
      origin: "discover", status: "new", triaged_at: new Date().toISOString(), discovery,
    });
    // The relevance decision is its triage (never a draft until she joins).
    await db.from("items").update({ triage: discoveryTriage(discovery) }).eq("id", r.id).is("triage", null);
    const { data: row } = await db.from("items").select("*").eq("id", r.id).single();
    results.push(row);
  }
  return { scanned: uniq.length, matched: matched.length, results, errors };
});
