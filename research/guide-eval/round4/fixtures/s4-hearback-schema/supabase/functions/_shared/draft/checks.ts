// The [check: …] gaps in a draft as structured checks. A gap is a question
// only she can answer (a fact the model couldn't know, an experience it can't
// vouch for). Each one has an id, the question, and its exact span in the
// text, so the app can show it as a card and the server can resolve exactly
// that place. Pure; tested. The app parses the same way (Dart: DraftChecks).

export interface CheckSpan {
  /** "c1", "c2", … in text order. Stable for one text (one draft version + her edits). */
  id: string;
  /** The question inside the marker, trimmed ("did you try X? what happened"). */
  question: string;
  /** UTF-16 offsets into the text (JavaScript and Dart index strings the same way). end is exclusive. */
  start: number;
  end: number;
  /** The marker exactly as it is in the text, "[check: …]". */
  marker: string;
}

/** A complete marker. The question can't contain "]". */
export const CHECK_MARKER = /\[check:[^\]]*\]/gi;

/** Any trace of a marker, complete or not: what posting refuses. */
export const CHECK_TRACE = /\[check/i;

export function parseChecks(text: string): CheckSpan[] {
  const out: CheckSpan[] = [];
  for (const m of text.matchAll(CHECK_MARKER)) {
    const start = m.index!;
    out.push({
      id: `c${out.length + 1}`,
      question: m[0].replace(/^\[\s*check:\s*/i, "").replace(/\]\s*$/, "").trim(),
      start,
      end: start + m[0].length,
      marker: m[0],
    });
  }
  return out;
}

/** True while the text still has a gap (also a half-deleted "[check …"). Posting refuses it. */
export function hasUnresolvedCheck(text: string): boolean {
  return CHECK_TRACE.test(text);
}
