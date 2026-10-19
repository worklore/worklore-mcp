// The core data a connector hands over, and the connector contract.
// docs/ARCHITECTURE.md › 2. Nothing here names a platform.

export type ItemKind = "comment" | "reply" | "mention" | "quote" | "post";

/** Who wrote it, on that platform. Becomes an identity (and a person). */
export interface NormalizedAuthor {
  handle: string;
  external_id?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
  profile_url?: string | null;
}

export interface ThreadMessage {
  author: string;
  text: string;
  posted_at?: string;
  is_owner: boolean;
}

export interface MyPost {
  title?: string | null;
  url: string;
  text: string;
  author?: string | null;
  is_owner: boolean;
}

/** One incoming message addressed to (or found for) the founder. */
export interface NormalizedItem {
  platform: string;
  external_id: string;
  kind: ItemKind;
  author: NormalizedAuthor;
  text: string;
  url: string | null;
  posted_at: string;
  thread: ThreadMessage[];
  my_post: MyPost | null;
  /** Opaque to the core; read back only by the same connector to reply. */
  reply_target: { root: unknown; parent: unknown };
  /** She already answered it on the platform. */
  answered?: boolean;
}

/** The founder's own message seen while syncing: an `out` touch, never an item. */
export interface OwnMessage {
  platform: string;
  external_id: string;
  kind: string;
  /** The handle she answered (or whose post she commented on). */
  to_handle: string | null;
  url: string | null;
  text: string;
  posted_at: string;
  /** The item she answered, if it may be stored: it becomes `answered`. */
  answers_external_id?: string | null;
}

/** What one sync (or one ingest call) produced for one account. */
/** normalizeIngest's result: the batch, and the raw items it rejected. */
export interface NormalizedIngest {
  batch: SyncBatch;
  rejected: { index: number; reason: string }[];
}

export interface SyncBatch {
  items: NormalizedItem[];
  own: OwnMessage[];
  /** Account fields to write after storing (cursor, settings, external_id); settings are merged. */
  account?: { cursor?: string | null; settings?: Record<string, unknown>; external_id?: string | null; drop_settings?: string[] };
  /** Connector-specific counters for the response (e.g. articles read). */
  stats?: Record<string, number>;
  /** Set when the connector skipped this account (backoff, …). */
  skipped?: string;
  /** External ids the network shows as hidden by her (dev.to "[hidden by post author]"): done in Hearback. */
  hidden?: { platform: string; external_ids: string[] };
}

export interface AccountRow {
  id: string;
  project_id: string;
  platform: string;
  handle: string;
  external_id?: string | null;
  cursor?: string | null;
  settings?: Record<string, unknown> | null;
  secret_id?: string | null;
}

export interface ItemRow {
  id: string;
  project_id: string;
  platform: string;
  account_id: string | null;
  kind: string;
  external_id: string;
  root_ref: unknown;
  parent_ref: unknown;
}

export interface RateLimitPolicy {
  /** Minimum gap between two requests to the platform. */
  minIntervalMs: number;
  /** Hard cap of platform requests in one worker run (all accounts). */
  maxRequestsPerRun: number;
  /** What a 429 does: wait Retry-After and retry, or back the account off until the reset. */
  on429: "retry_after" | "backoff_account";
}

export interface Connector {
  /** = items.platform, accounts.platform. */
  id: string;
  label: string;
  /** How the founder connects (descriptive). */
  auth: "none" | "app_password" | "device_session" | "oauth" | "api_key";
  /** accounts.auth value for rows this connector creates. */
  accountAuth: "none" | "oauth" | "app_password" | "api_key";
  /** Only accounts with a stored secret are polled. */
  needsSecret: boolean;
  /** Feature flag. A disabled connector neither polls, connects nor posts. */
  enabled(): boolean;
  /** Its own pg_cron job (null: not scheduled). */
  schedule: { job: string; cron: string } | null;
  rateLimit: RateLimitPolicy;
  reply: { mode: "server" | "device" | "none"; maxGraphemes: number | null };

  /** Per-run state shared by the accounts of one worker run (e.g. a rate-limited HTTP client). */
  beginRun?(): unknown;
  /** Server-side polling of one account. */
  sync?(account: AccountRow, ctx: SyncContext): Promise<SyncBatch>;
  /** Items the phone read with its own session (`ingest`): raw → normalized (may read the public API to fill what the phone can't see). */
  normalizeIngest?(raw: unknown[], account: AccountRow, ctx?: { run?: unknown }): NormalizedIngest | Promise<NormalizedIngest>;
  /** Reply on the platform (reply.mode "server"). */
  postReply?(account: AccountRow, item: ItemRow, text: string): Promise<{ url: string; external_id: string }>;

  // ---- sources (docs/ARCHITECTURE.md › Sources: voice and knowledge); all optional
  /** The founder's own past replies/comments/posts on this platform: voice-sample candidates. */
  ownWriting?(account: AccountRow, ctx: SourceContext): Promise<SourceBatch>;
  /** Her published long-form work (articles) by this account: knowledge documents. */
  publishedWork?(account: AccountRow, ctx: SourceContext): Promise<SourceBatch>;
  /** A project-level source not tied to an account (GitHub: the linked repo's folder). */
  projectSource?(project: ProjectSourceRow, ctx: SourceContext): Promise<SourceBatch>;
}

/** One piece of the founder's own writing (a voice-sample candidate). */
export interface OwnWriting {
  platform: string;
  /** Platform id, stable across runs (dedupe). */
  external_id: string;
  url: string | null;
  text: string;
  posted_at: string | null;
  /** What it replied to, or the article / file it sits in. */
  context?: string | null;
}

/** One whole document for the knowledge base (the core chunks it). */
export interface SourceDocument {
  kind: "article" | "story" | "research" | "changelog" | "readme" | "faq" | "docs" | "fact" | "page";
  title: string;
  /** Public link (also the dedupe key per project). */
  url: string;
  published_at: string;
  /** Markdown or plain text. */
  markdown: string;
  lang?: string;
  /** quotable = public work she may quote and link; background = context only. */
  label?: "quotable" | "background";
}

/** What one source run produced. */
export interface SourceBatch {
  writing?: OwnWriting[];
  documents?: SourceDocument[];
  /** Saved as source_syncs.state for the next run (ETags, SHAs, counts). */
  state?: Record<string, unknown>;
  /** ok, or why the source could not be read (needs_auth: private repo without GitHub sign-in). */
  status?: "ok" | "error" | "needs_auth" | "rate_limited" | "empty";
  message?: string | null;
  stats?: Record<string, number>;
}

/** The project fields project-level sources read. */
export interface ProjectSourceRow {
  id: string;
  url?: string | null;
  github_repo?: string | null;
  github_folder?: string | null;
}

export interface SourceContext {
  /** This source's state from the previous run (source_syncs.state). */
  state: Record<string, unknown>;
  /** Which of these external ids are already stored as voice samples (skip refetching them). */
  knownWriting(platform: string, externalIds: string[]): Promise<Set<string>>;
  /** References the phone read with its own session (e.g. dev.to: links to her comments), if any. */
  deviceRefs?: unknown[];
  /** Epoch ms after which the source should stop and return what it has. */
  deadline: number;
}

export interface SyncContext {
  /** Per-run state from beginRun(). */
  run: unknown;
  /** Which of these external ids the project already has (skip re-reading their threads). */
  known(projectId: string, externalIds: string[]): Promise<Set<string>>;
}
