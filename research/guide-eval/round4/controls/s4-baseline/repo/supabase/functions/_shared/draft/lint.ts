// Clean-up of model output and a lint report the app can show next to the draft
// ("1 thing to check", "contains 'Great question'"). Clean-up only removes
// wrapping the model adds around the draft; it never rewrites her sentences.

import { BANNED_PHRASES, PROMISE_PATTERNS } from "./prompt.ts";
import { detectLanguage, words } from "./text.ts";
import type { LintReport } from "./types.ts";

export function cleanDraft(raw: string, founderName?: string | null): string {
  let t = raw.trim();
  t = t.replace(/^```[a-z]*\n([\s\S]*?)\n```$/i, "$1").trim();
  t = t.replace(/^(here'?s|here is) (a |my |the )?(draft|reply|response)[^:\n]*:\s*/i, "");
  t = t.replace(/^(draft|reply|response)\s*:\s*/i, "");
  if (/^".*"$/s.test(t) && !t.slice(1, -1).includes('"')) t = t.slice(1, -1).trim();
  if (founderName) {
    const first = founderName.split(/\s+/)[0];
    t = t.replace(new RegExp(`\\n+\\s*(?:[-—–]\\s*|(?:best|cheers|thanks|regards),?\\s*\\n?\\s*)${first}\\b.*$`, "i"), "");
  }
  return t.replace(/\n{3,}/g, "\n\n").trim();
}

/** First-person reports of action ("I ran…", "I added…") — the claims only she can vouch for. */
const ACTION = /\bI(?:'ve| have)?\s+(?:also\s+|already\s+|just\s+)?(ran|tried|added|built|checked|moved|fixed|updated|found|measured|integrated|implemented|switched|shipped|tested|wrote|published|replaced|recorded|hit)\b/i;

/**
 * Sentences where she reports doing something ("I ran…", "I added…") that the
 * context doesn't show. The model can't know what she did, so every such
 * sentence needs her confirmation unless it carries a [check: …] slot or is
 * lifted from the context (shares a 5-word run with it: her earlier reply,
 * the thread, project notes). For the UI to highlight, not to block.
 */
export function unverifiedClaims(text: string, contextText: string): string[] {
  const norm = (s: string) => s.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ").split(/\s+/).filter(Boolean);
  const ctx = new Set<string>();
  const cw = norm(contextText);
  for (let i = 0; i + 5 <= cw.length; i++) ctx.add(cw.slice(i, i + 5).join(" "));
  return text.split(/(?<=[.!?])\s+|\n+/).map((s) => s.trim()).filter((s) => {
    if (!ACTION.test(s) || /\[check:/i.test(s)) return false;
    const w = norm(s);
    for (let i = 0; i + 5 <= w.length; i++) if (ctx.has(w.slice(i, i + 5).join(" "))) return false;
    return true;
  });
}

/** URLs (or bare domain/path links) in the draft that the context never shows: likely invented. */
export function unknownLinks(text: string, contextText: string): string[] {
  const norm = (u: string) => u.replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/[).,;:!?'"\]]+$/, "").replace(/\/$/, "");
  const ctx = contextText.replace(/https?:\/\//g, "").replace(/www\./g, "");
  const links = text.match(/https?:\/\/[^\s)\]]+|\b(?:[a-z0-9-]+\.)+(?:dev|com|io|org|ru|ai|app|net)\/[^\s)\]]*/gi) ?? [];
  return [...new Set(links)].filter((l) => !ctx.includes(norm(l)));
}

export function lint(text: string, comment: string, target: [number, number], contextText = ""): LintReport {
  const lower = text.toLowerCase();
  return {
    unknown_links: contextText ? unknownLinks(text, contextText) : [],
    unverified_claims: contextText ? unverifiedClaims(text, contextText) : [],
    placeholders: text.match(/\[check:[^\]]*\]/gi) ?? [],
    banned_phrases: BANNED_PHRASES.filter((p) => new RegExp(`(^|[^a-z])${p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}([^a-z]|$)`).test(lower)),
    promises: PROMISE_PATTERNS.flatMap((re) => text.match(re)?.[0] ?? []),
    em_dashes: (text.match(/—/g) ?? []).length,
    words: words(text),
    target_words: target,
    language: detectLanguage(comment),
  };
}
