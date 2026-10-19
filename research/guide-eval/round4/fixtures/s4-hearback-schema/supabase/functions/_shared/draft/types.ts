// Data the draft engine works with. Every field maps to a column of the v1
// schema (supabase/migrations/20261008170000_init.sql); load.ts does the mapping.
// The engine itself never touches the database, so it runs the same in an Edge
// Function, a script, or the eval.

export type Platform = "bluesky" | "devto" | "github" | "threads" | "habr" | "reddit" | "x" | "email" | "other";

/** projects row (+ founders.voice_notes of whoever answers). */
export interface ProjectProfile {
  name: string;
  one_liner?: string | null;
  audience?: string | null;
  /** What the project is trying to achieve right now; article triage judges relevance against it. */
  aims?: string | null;
  views?: string | null;          // positions the team holds
  red_lines?: string | null;      // never promise / never say
  tone?: string | null;
  links?: { title: string; url: string }[];
  founder_name?: string | null;
  founder_handle?: string | null;
  voice_notes?: string | null;    // founders.voice_notes
}

/** One message in the thread above the item (items.thread / my_post). */
export interface ThreadMessage {
  author: string;
  text: string;
  posted_at?: string;
  is_owner?: boolean;             // written by the founder (or the project account)
}

/** The item to answer, with everything above it. */
export interface ItemContext {
  platform: Platform;
  kind: "reply" | "mention" | "quote" | "comment";
  post?: { title?: string; url?: string; text: string; author?: string; is_owner?: boolean } | null; // items.my_post, or the article she comments on
  chain: ThreadMessage[];         // parent chain, oldest first, NOT including the item itself
  item: ThreadMessage;            // the comment/reply that needs an answer
}

/** A real past reply of the founder: project_memory(kind='voice_sample') or a posted draft's final_text. */
export interface VoiceSample {
  id: string;
  text: string;                   // what she wrote
  in_reply_to?: string;           // short excerpt of what it answered (helps the model see the move)
  theme?: string;
  posted_at?: string;
}

/** people row + recent touches. */
export interface PersonContext {
  handle: string;
  display_name?: string | null;
  summary?: string | null;
  builds?: string | null;
  cares_about?: string | null;
  stage?: string | null;
  notes?: string | null;
  touches?: { direction: "in" | "out"; text: string; occurred_at: string; url?: string | null }[];
}

/** project_memory rows that are not voice samples (fact / position / faq / need / preference). */
export interface MemorySnippet {
  id: string;
  kind: "preference" | "need" | "faq" | "fact" | "position";
  text: string;
  source_url?: string | null;
  theme?: string | null;
}

export type Variant = "first" | "shorter" | "redraft";

/** Where a knowledge chunk came from (document_chunks.kind). */
export type KnowledgeKind = "article" | "story" | "research" | "changelog" | "readme" | "faq" | "docs" | "fact" | "page";

/**
 * One retrieved piece of the founder's published body of work: an article
 * section, a story, a research report section, a run of release notes.
 * The caller retrieves (retrieve.ts) and date-filters; the engine only packs.
 */
export interface KnowledgeChunk {
  id: string;
  kind: KnowledgeKind;
  title: string;
  /** Public link a draft may cite. null = not public (e.g. a private repo); never linked. */
  source_url: string | null;
  /** Where it came from when there's no public URL (repo path), for the "why this draft" view. */
  source_ref?: string;
  /** When this text became public (ISO date or datetime). Retrieval drops anything not before the item. */
  published_at: string;
  text: string;
  tokens: number;
  lang?: string;
  /** Similarity to the item, set by retrieval. */
  score?: number;
}

/** Triage kind of an incoming item (triage.ts); the draft's shape depends on it. */
export type ItemKind = "feedback" | "engagement" | "question" | "reaction";

export interface DraftRequest {
  project: ProjectProfile;
  context: ItemContext;
  person?: PersonContext | null;
  /** Candidate pool; the engine picks 3–6 by similarity. Caller must exclude anything not yet written at the item's time. */
  voice_pool: VoiceSample[];
  /** Candidate pool; the engine retrieves the 2–3 most relevant. */
  memory_pool: MemorySnippet[];
  /** Retrieved chunks of her published work, best first, already date-filtered (retrieve.ts). Prompt v4 uses them. */
  knowledge?: KnowledgeChunk[];
  /** Triage kind (triage.ts). Shapes the draft: question → answer with a source, reaction → 1–3 sentences. */
  item_kind?: ItemKind | null;
  variant?: Variant;
  /** For shorter/redraft: the draft being revised (or replaced). */
  previous_draft?: string | null;
  /** Free-text note from the founder ("mention the Habr article", "less formal"). */
  note?: string | null;
  /** Her point for this reply, in her words (the redraft prompt in the app). A redraft is built on it. */
  gist?: string | null;
  /** Redraft only: grow a one-line draft into a full reply with the same point (Longer). */
  expand?: boolean;
}

export interface Usage {
  tokens_in: number | null;
  tokens_out: number | null;
  /** Provider's breakdown (cache reads/writes, cost) → drafts.tokens. */
  detail?: { input: number; output: number; cache_read?: number; cache_write?: number; cost_usd?: number };
}

export interface DraftResult {
  text: string;
  provider: string;
  model: string;
  usage: Usage;
  latency_ms: number;
  /** drafts.instruction: null for the first draft, 'shorter' / 'redraft' / the note. */
  instruction: string | null;
  lint: LintReport;
  /** What went into the prompt, for debugging and for the app's "why this draft" view. */
  context_report: ContextReport;
}

export interface LintReport {
  placeholders: string[];         // [check: …] markers left for the founder
  banned_phrases: string[];       // phrases from the never-say list that slipped through
  unverified_claims: string[];    // "I ran X…" sentences the context doesn't support: ask her before posting
  promises: string[];             // future commitments ("I'll update…") she should confirm or cut
  /** Links in the draft that appear nowhere in the context (invented URLs). */
  unknown_links: string[];
  /** Numbers / statistics / cited studies the fact guard turned into [check: …] gaps (guard.ts). */
  invented_facts?: string[];
  em_dashes: number;
  words: number;
  target_words: [number, number];
  language: string;               // detected language of the comment
}

export interface ContextReport {
  budget_tokens: number;
  used_tokens: number;
  sections: { name: string; tokens: number; dropped?: boolean; truncated?: boolean }[];
  voice_sample_ids: string[];
  memory_ids: string[];
  knowledge_ids?: string[];
  prompt_version?: string;
}
