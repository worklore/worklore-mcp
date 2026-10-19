// Knowledge base storage: SourceDocuments from the sources pipeline
// (core/sources/run.ts) → documents + document_chunks, then embeddings.
// Idempotent: each document carries a hash of what produced its chunks, so a
// re-run skips unchanged documents entirely and keeps embeddings of unchanged
// chunks of a changed one. A privacy scan drops chunks with emails or
// secret-like strings.
//
// Which sources exist is not configured per project any more
// (projects.knowledge_sources was the one-off seed path): connectors bring
// published work, GitHub brings the project folder, the landing crawl brings
// the site. Documents only the seed produced are marked source = 'seed'.

import { chunkMarkdown, cleanMarkdown } from "../draft/chunk.ts";
import type { SourceDocument } from "../core/types.ts";
import { admin } from "./ctx.ts";
import { embedder, toVector } from "./models.ts";

const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}/g;
const SECRETISH = /(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|aws ssm|get-parameter|BEGIN [A-Z ]*PRIVATE KEY)/i;
/** Pure. Why a chunk must not be stored (emails, secret-like strings); [] = fine. */
export function privacyFlags(text: string): string[] {
  const f: string[] = [];
  const emails = (text.match(EMAIL) ?? []).filter((e) => !/@\d/.test(e) && !/^(io\.github|worklore)@/.test(e));
  if (emails.length) f.push("email");
  if (SECRETISH.test(text)) f.push("secret-like");
  return f;
}

export async function sha256(s: string) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** The hash of everything that shapes a document's chunks and rows. */
export const docSha = (d: SourceDocument) =>
  sha256([d.kind, d.title, d.published_at, d.label ?? "quotable", d.lang ?? "en", d.markdown].join("\n\u0000"));

export interface ExistingDoc { url: string; content_sha256: string | null; source: string | null }
export interface IncomingDoc { url: string; sha: string; source: string }

/**
 * Pure. What a run must do per document: `write` new or changed ones (chunks
 * replaced), only `relabel` an unchanged one whose source differs (e.g. a seed
 * document the pipeline now reproduces byte for byte), leave the rest.
 */
export function planDocs(existing: ExistingDoc[], incoming: IncomingDoc[]) {
  const old = new Map(existing.map((e) => [e.url, e]));
  const seen = new Set<string>();
  const write: string[] = [], relabel: string[] = [], unchanged: string[] = [];
  for (const d of incoming) {
    if (seen.has(d.url)) continue; // first source wins within a run
    seen.add(d.url);
    const e = old.get(d.url);
    if (!e || e.content_sha256 !== d.sha) write.push(d.url);
    else if (e.source !== d.source) relabel.push(d.url);
    else unchanged.push(d.url);
  }
  return { write, relabel, unchanged };
}

export interface StoreReport {
  documents: number; written: number; unchanged: number; relabeled: number;
  chunks: number; reused_embeddings: number; dropped_for_privacy: number;
}

/** Upserts what changed; keeps embeddings of unchanged chunks (same chunk sha). */
export async function storeDocs(projectId: string, docs: { doc: SourceDocument; source: string }[]): Promise<StoreReport> {
  const db = admin();
  const withSha = await Promise.all(docs.map(async (x) => ({ ...x, sha: await docSha(x.doc) })));
  const { data: existing, error: e0 } = await db.from("documents").select("url, content_sha256, source").eq("project_id", projectId);
  if (e0) throw e0;
  const plan = planDocs(existing ?? [], withSha.map((x) => ({ url: x.doc.url, sha: x.sha, source: x.source })));
  const byUrl = new Map(withSha.map((x) => [x.doc.url, x]));
  for (const url of plan.relabel) {
    await db.from("documents").update({ source: byUrl.get(url)!.source }).eq("project_id", projectId).eq("url", url);
  }
  const keep = new Map<string, { embedding: unknown; model: string }>();
  if (plan.write.length) {
    const { data: old } = await db.from("document_chunks").select("content_sha256, embedding, embedding_model").eq("project_id", projectId)
      .not("embedding", "is", null);
    for (const r of old ?? []) keep.set(r.content_sha256, { embedding: r.embedding, model: r.embedding_model });
  }
  let chunks = 0, reused = 0, dropped = 0;
  for (const url of plan.write) {
    const { doc: d, source, sha } = byUrl.get(url)!;
    const raw = chunkMarkdown(d.title, cleanMarkdown(d.markdown));
    const day = d.published_at.length <= 10;
    const published = day ? `${d.published_at}T00:00:00Z` : d.published_at;
    const label = d.label ?? "quotable";
    const { data: row, error } = await db.from("documents").upsert({
      project_id: projectId, kind: d.kind, url: d.url, title: d.title, content: raw.map((c) => c.text).join("\n\n"),
      fetched_at: new Date().toISOString(), published_at: published, published_precision: day ? "day" : "instant",
      source, content_sha256: sha, label,
    }, { onConflict: "project_id,url" }).select("id").single();
    if (error) throw error;
    const rows = [];
    for (const [i, c] of raw.entries()) {
      if (privacyFlags(c.text).length) { dropped++; continue; }
      const csha = await sha256(`${c.title}\n${c.text}`);
      const k = keep.get(csha);
      if (k) reused++;
      rows.push({
        // kind, label and the source link come from the document (match_document_chunks joins it).
        project_id: projectId, document_id: row.id, ord: i, title: c.title,
        published_at: published, published_precision: day ? "day" : "instant",
        content: c.text, content_sha256: csha, tokens: c.tokens, lang: d.lang ?? "en",
        embedding: k?.embedding ?? null, embedding_model: k?.model ?? null,
      });
    }
    await db.from("document_chunks").delete().eq("document_id", row.id);
    if (rows.length) {
      const { error: e2 } = await db.from("document_chunks").insert(rows);
      if (e2) throw e2;
    }
    chunks += rows.length;
  }
  return {
    documents: plan.write.length + plan.relabel.length + plan.unchanged.length, written: plan.write.length,
    unchanged: plan.unchanged.length, relabeled: plan.relabel.length, chunks, reused_embeddings: reused, dropped_for_privacy: dropped,
  };
}

/** Documents no pipeline source produced (the one-off seed): kept and retrieved, labeled 'seed'. */
export async function markSeed(projectId: string): Promise<number> {
  const { data, error } = await admin().from("documents").update({ source: "seed" }).eq("project_id", projectId).is("source", null).select("id");
  if (error) throw error;
  return data?.length ?? 0;
}

/** Embeds chunks that have none, 25 per request with pauses (free-tier per-minute quota), until the deadline. */
export async function embedPending(projectId: string, deadline: number) {
  const db = admin();
  const emb = embedder();
  let embedded = 0;
  while (Date.now() < deadline - 25_000) {
    const { data } = await db.from("document_chunks").select("id, title, content").eq("project_id", projectId).is("embedding", null).limit(25);
    if (!data?.length) break;
    const vecs = await emb.embed(data.map((c) => c.content), "document", data.map((c) => c.title));
    for (const [i, c] of data.entries()) {
      await db.from("document_chunks").update({ embedding: toVector(vecs[i]), embedding_model: `${emb.model}@${emb.dims}` }).eq("id", c.id);
    }
    embedded += data.length;
    if (Date.now() < deadline - 40_000) await new Promise((r) => setTimeout(r, 25_000));
  }
  const { count } = await db.from("document_chunks").select("id", { count: "exact", head: true }).eq("project_id", projectId).is("embedding", null);
  return { embedded, pending: count ?? 0 };
}
