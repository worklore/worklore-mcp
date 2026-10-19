// dev.to comments → ParsedComment: from the public API's comment tree
// (flattenTree) or from the phone's `ingest` items (parseIngestItem). Pure; tested.

import { htmlToText, markdownToText } from "../../server/text.ts";
import type { DevtoArticle, DevtoCommentNode } from "./api.ts";

/** One comment as Hearback stores it; also the `ingest` request item shape (after normalising). */
export interface ParsedComment {
  id_code: string;
  kind: "comment" | "reply" | "mention";
  text: string;
  url: string;
  created_at: string;
  author: { username: string; name?: string | null; avatar_url?: string | null; profile_url?: string | null };
  article: { id: number | string; title: string; url: string; author_username?: string | null; text?: string | null };
  parent?: { id_code: string; text: string; author_username?: string | null } | null;
  /** Ancestors, oldest first (when known from the tree). */
  thread?: { author: string; text: string; posted_at?: string }[];
  top_id_code?: string;
  /** The founder already replied under it (from the tree). */
  answered_by_owner?: boolean;
  /** Some ancestor is the founder's comment (a reply inside her thread). */
  under_owner?: boolean;
}

/** What dev.to's API shows instead of a comment the article's author hid. */
export const HIDDEN_BODY = "[hidden by post author]";

/** Pure: id codes of comments in the tree that the article's author hid (they come with no user). */
export function hiddenIn(tree: DevtoCommentNode[]): string[] {
  const out: string[] = [];
  const walk = (nodes: DevtoCommentNode[]) => {
    for (const n of nodes) {
      if (htmlToText(n.body_html ?? "").trim() === HIDDEN_BODY) out.push(n.id_code);
      walk(n.children ?? []);
    }
  };
  walk(tree);
  return out;
}

/** Pure: a comment tree → every comment with its ancestors. Exported for tests. */
export function flattenTree(article: Pick<DevtoArticle, "id" | "title" | "url" | "description" | "body_markdown" | "user">, owner: string,
  tree: DevtoCommentNode[]): ParsedComment[] {
  const out: ParsedComment[] = [];
  const own = owner.toLowerCase();
  const walk = (nodes: DevtoCommentNode[], chain: { node: DevtoCommentNode; text: string }[]) => {
    for (const n of nodes) {
      if (!n.user?.username) { walk(n.children ?? [], chain); continue; } // deleted
      const text = htmlToText(n.body_html ?? "");
      const parent = chain.at(-1);
      out.push({
        id_code: n.id_code,
        kind: (parent?.node.user?.username?.toLowerCase() === own ? "reply" : "comment") as ParsedComment["kind"],
        text,
        url: `https://dev.to/${n.user.username}/comment/${n.id_code}`,
        created_at: n.created_at,
        author: {
          username: n.user.username, name: n.user.name ?? null,
          avatar_url: n.user.profile_image_90 ?? n.user.profile_image ?? null, profile_url: `https://dev.to/${n.user.username}`,
        },
        article: {
          id: article.id, title: article.title, url: article.url, author_username: article.user?.username ?? owner,
          text: article.body_markdown ? markdownToText(article.body_markdown).slice(0, 4000) : article.description ?? null,
        },
        parent: parent ? { id_code: parent.node.id_code, text: parent.text, author_username: parent.node.user?.username ?? null } : null,
        thread: chain.map((c) => ({ author: c.node.user?.username ?? "deleted", text: c.text, posted_at: c.node.created_at })),
        top_id_code: chain[0]?.node.id_code ?? n.id_code,
        answered_by_owner: (n.children ?? []).some((ch) => ch.user?.username?.toLowerCase() === own),
        under_owner: chain.some((c) => c.node.user?.username?.toLowerCase() === own),
      });
      walk(n.children ?? [], [...chain, { node: n, text }]);
    }
  };
  walk(tree, []);
  return out;
}

/** Normalises one `ingest` request item (from the phone). Throws a message on bad input. Pure; tested. */
export function parseIngestItem(raw: Record<string, unknown>): ParsedComment {
  const s = (v: unknown) => (typeof v === "string" ? v : v === undefined || v === null ? "" : String(v));
  const a = (raw.author ?? {}) as Record<string, unknown>;
  const art = (raw.article ?? {}) as Record<string, unknown>;
  const par = raw.parent as Record<string, unknown> | undefined | null;
  const id = s(raw.id_code).trim();
  const user = s(a.username).trim().replace(/^@/, "");
  if (!/^[a-z0-9]{1,16}$/i.test(id)) throw new Error("id_code missing or invalid");
  if (!user) throw new Error("author.username missing");
  const fmt = s(raw.text_format) || "markdown";
  const body = s(raw.text);
  if (!body.trim()) throw new Error("text missing");
  const text = fmt === "html" ? htmlToText(body) : fmt === "plain" ? body.trim() : markdownToText(body);
  const created = new Date(s(raw.created_at));
  if (isNaN(created.getTime())) throw new Error("created_at invalid");
  return {
    id_code: id,
    kind: raw.kind === "mention" ? "mention" : raw.kind === "reply" ? "reply" : "comment",
    text: text.slice(0, 20_000),
    url: s(raw.url) || `https://dev.to/${user}/comment/${id}`,
    created_at: created.toISOString(),
    author: {
      username: user, name: s(a.name) || null, avatar_url: s(a.avatar_url) || null,
      profile_url: s(a.profile_url) || `https://dev.to/${user}`,
    },
    article: { id: s(art.id), title: s(art.title), url: s(art.url), author_username: s(art.author_username) || null, text: s(art.text) || null },
    parent: par && s(par.id_code) ? { id_code: s(par.id_code), text: s(par.text), author_username: s(par.author_username) || null } : null,
  };
}
