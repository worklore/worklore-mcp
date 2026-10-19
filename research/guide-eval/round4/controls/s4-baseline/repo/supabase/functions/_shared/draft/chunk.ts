// Markdown → retrieval chunks of ~300–600 tokens. Splits on blank lines, keeps
// fenced code and tables whole where they fit, carries the current heading
// into the chunk title, and records each chunk's source line range so a caller
// can date it (git blame: a chunk is as new as its newest line).

import { estimateTokens } from "./text.ts";

export interface RawChunk {
  title: string;        // "Doc title › Section heading"
  text: string;
  tokens: number;
  lines: [number, number]; // 1-based, inclusive, in the cleaned input
}

export interface ChunkOptions {
  minTokens?: number; // 300
  maxTokens?: number; // 600
}

/** Remove what retrieval can't use: front matter, images, HTML comments, liquid tags, link targets of images. */
export function cleanMarkdown(md: string): string {
  return md
    .replace(/^---\n[\s\S]*?\n---\n/, (m) => "\n".repeat(m.split("\n").length - 1))
    .replace(/<!--[\s\S]*?-->/g, (m) => "\n".repeat(m.split("\n").length - 1))
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\{%[^%]*%\}/g, "")
    .replace(/[ \t]+$/gm, "");
}

export function chunkMarkdown(docTitle: string, md: string, opts: ChunkOptions = {}): RawChunk[] {
  const min = opts.minTokens ?? 300, max = opts.maxTokens ?? 600;
  const lines = md.split("\n");
  // Blocks: runs of non-blank lines; a fenced code block is one block even with blank lines inside.
  type Block = { text: string; from: number; to: number; heading?: string };
  const blocks: Block[] = [];
  let cur: string[] = [], from = 0, inFence = false;
  const flush = (i: number) => {
    if (cur.join("").trim()) blocks.push({ text: cur.join("\n").trim(), from: from + 1, to: i });
    cur = [];
  };
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (/^\s*```/.test(l)) inFence = !inFence;
    if (!inFence && !l.trim()) { flush(i); from = i + 1; continue; }
    if (!inFence && /^#{1,4}\s/.test(l)) { flush(i); from = i; cur = [l]; flush(i + 1); from = i + 1; continue; }
    if (!cur.length) from = i;
    cur.push(l);
  }
  flush(lines.length);
  for (const b of blocks) if (/^#{1,4}\s/.test(b.text)) b.heading = b.text.replace(/^#+\s*/, "").trim();

  // Oversized blocks (long tables, long code) are split by lines.
  const sized: Block[] = [];
  for (const b of blocks) {
    if (estimateTokens(b.text) <= max) { sized.push(b); continue; }
    const ls = b.text.split("\n");
    let acc: string[] = [], start = b.from;
    for (let j = 0; j < ls.length; j++) {
      if (acc.length && estimateTokens([...acc, ls[j]].join("\n")) > max) {
        sized.push({ text: acc.join("\n"), from: start, to: b.from + j - 1 });
        acc = []; start = b.from + j;
      }
      acc.push(ls[j]);
    }
    if (acc.length) sized.push({ text: acc.join("\n"), from: start, to: b.to });
  }

  const out: RawChunk[] = [];
  let heading = "";
  let buf: Block[] = [];
  const size = (bs: Block[]) => estimateTokens(bs.map((x) => x.text).join("\n\n"));
  const hasBody = () => buf.some((b) => !b.heading);
  const emit = () => {
    if (hasBody()) {
      const text = buf.map((b) => b.text).join("\n\n");
      out.push({ title: heading ? `${docTitle} › ${heading}` : docTitle, text, tokens: estimateTokens(text), lines: [buf[0].from, buf.at(-1)!.to] });
    }
    buf = [];
  };
  for (const b of sized) {
    if (b.heading) {
      // A new section starts a new chunk once the current one is big enough;
      // a short section is merged forward instead of becoming a stub.
      if (hasBody() && size(buf) >= min * 0.5) emit();
      if (!hasBody()) { buf = []; heading = b.heading; }
      buf.push(b);
      continue;
    }
    if (hasBody() && size([...buf, b]) > max) emit();
    buf.push(b);
  }
  emit();

  // Merge a tiny tail into its predecessor when both fit.
  for (let i = out.length - 1; i > 0; i--) {
    if (out[i].tokens < min * 0.4 && out[i - 1].tokens + out[i].tokens <= max * 1.1 && out[i].title.split(" › ")[0] === out[i - 1].title.split(" › ")[0]) {
      const a = out[i - 1], b = out[i];
      const text = `${a.text}\n\n${b.text}`;
      out.splice(i - 1, 2, { title: a.title, text, tokens: estimateTokens(text), lines: [a.lines[0], b.lines[1]] });
    }
  }
  return out;
}
