// Pure parts of the GitHub folder source: which files to (re)read, and how a
// file becomes a knowledge document plus voice-sample candidates. Tested with
// fixtures (sources_test.ts).

import type { OwnWriting, SourceDocument } from "../../core/types.ts";

export const GITHUB_CAPS = {
  /** A file bigger than this is skipped (not her message; maybe a dump). */
  maxFileBytes: 100_000,
  /** Files considered in the folder. */
  maxFiles: 50,
  /** Bytes read per run. */
  maxRunBytes: 1_000_000,
  /** Changed files read per run (each costs one API call for its commit date; 60/h unauthenticated). */
  maxChangedPerRun: 10,
  /** Voice candidates per file, and per run (each one is a decider call). */
  maxWritingPerFile: 10,
  maxWritingPerRun: 60,
};

const TEXT_EXT = /\.(md|markdown|txt)$/i;

export interface TreeEntry { path: string; type: string; sha: string; size?: number }

export interface SyncPlan {
  /** Files to read now (new or changed blob sha). */
  read: TreeEntry[];
  /** Same blob sha as last run. */
  unchanged: string[];
  /** Not read, with why: too_large, over_file_cap, run_byte_cap, run_file_cap (the last two: next run). */
  skipped: { path: string; reason: string }[];
}

/** Normalises a folder setting: no leading/trailing slashes; "" = repo root. */
export const folderPrefix = (folder: string | null | undefined) => {
  const f = (folder ?? "hearback").trim().replace(/^\/+|\/+$/g, "");
  return f ? `${f}/` : "";
};

/** Pure. Tree entries + last run's {path: blob sha} → what to read now. */
export function planGithubSync(tree: TreeEntry[], folder: string, prev: Record<string, string>, caps = GITHUB_CAPS): SyncPlan {
  const prefix = folderPrefix(folder);
  const files = tree.filter((e) => e.type === "blob" && e.path.startsWith(prefix) && TEXT_EXT.test(e.path))
    .sort((a, b) => a.path.localeCompare(b.path));
  const plan: SyncPlan = { read: [], unchanged: [], skipped: [] };
  let bytes = 0;
  for (const [i, f] of files.entries()) {
    if (i >= caps.maxFiles) { plan.skipped.push({ path: f.path, reason: "over_file_cap" }); continue; }
    if ((f.size ?? 0) > caps.maxFileBytes) { plan.skipped.push({ path: f.path, reason: "too_large" }); continue; }
    if (prev[f.path] === f.sha) { plan.unchanged.push(f.path); continue; }
    if (plan.read.length >= caps.maxChangedPerRun) { plan.skipped.push({ path: f.path, reason: "run_file_cap" }); continue; }
    if (bytes + (f.size ?? 0) > caps.maxRunBytes) { plan.skipped.push({ path: f.path, reason: "run_byte_cap" }); continue; }
    bytes += f.size ?? 0;
    plan.read.push(f);
  }
  return plan;
}

function stripFrontMatter(md: string) {
  return md.replace(/^﻿?---\n[\s\S]*?\n---\n/, "");
}

export function titleOf(md: string, path: string): string {
  const fm = md.match(/^\uFEFF?---\n([\s\S]*?)\n---\n/)?.[1]?.match(/^title:\s*["']?(.+?)["']?\s*$/m)?.[1]?.trim();
  const h = stripFrontMatter(md).match(/^#\s+(.+)$/m)?.[1]?.trim();
  return fm || h || path.split("/").pop()!.replace(TEXT_EXT, "").replace(/[-_]+/g, " ");
}

function shortHash(s: string): string {
  // FNV-1a, 32 bit: a stable id for a paragraph that survives reordering.
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); }
  return (h >>> 0).toString(16).padStart(8, "0");
}

const plain = (s: string) => s
  .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
  .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
  .replace(/^#{1,6}\s+/gm, "")
  .replace(/[*_`]{1,3}([^*_`]+)[*_`]{1,3}/g, "$1")
  .trim();

/**
 * Pure. A file's messages or paragraphs → voice candidates. A file whose
 * parts are separated by lines of `---` is a collection of messages (one
 * candidate each); otherwise every prose paragraph is one (headings, code,
 * tables and quotes skipped; under 15 words skipped).
 */
export function writingFromFile(md: string, meta: { repo: string; path: string; url: string; date: string }, cap = GITHUB_CAPS.maxWritingPerFile): OwnWriting[] {
  const body = stripFrontMatter(md).replace(/\r\n/g, "\n");
  const title = titleOf(md, meta.path);
  const isCollection = /\n-{3,}\s*\n/.test(`\n${body}\n`);
  let parts: string[];
  if (isCollection) {
    parts = `\n${body}\n`.split(/\n-{3,}\s*\n/).map((p) => p.trim());
  } else {
    parts = [];
    let inFence = false, cur: string[] = [];
    const flush = () => { if (cur.length) parts.push(cur.join("\n")); cur = []; };
    for (const l of body.split("\n")) {
      if (/^\s*```/.test(l)) { inFence = !inFence; flush(); continue; }
      if (inFence) continue;
      if (!l.trim()) { flush(); continue; }
      if (/^#{1,6}\s/.test(l) || /^\s*\|/.test(l) || /^\s*>/.test(l)) { flush(); continue; }
      cur.push(l);
    }
    flush();
  }
  const out: OwnWriting[] = [];
  const seen = new Set<string>();
  for (const p of parts) {
    const text = plain(p);
    if (text.split(/\s+/).filter(Boolean).length < 15) continue;
    const id = shortHash(text.replace(/\s+/g, " "));
    if (seen.has(id)) continue;
    seen.add(id);
    out.push({ platform: "github", external_id: `${meta.repo}:${meta.path}#${id}`, url: meta.url, text, posted_at: meta.date, context: `From "${title}" (${meta.path})` });
    if (out.length >= cap) break;
  }
  return out;
}

/** Pure. A file → its knowledge document (quotable: the repo is public). */
export function documentFromFile(md: string, meta: { path: string; url: string; date: string }): SourceDocument {
  return { kind: "article", title: titleOf(md, meta.path), url: meta.url, published_at: meta.date, markdown: stripFrontMatter(md), label: "quotable" };
}
