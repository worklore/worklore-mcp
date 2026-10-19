// deno test supabase/functions/_shared/core/ingest_context_test.ts   (no network)
// The phone's cut parent comment is replaced by the comment tree's full one,
// a re-read item keeps the richer thread, and a chip tap keeps the length.
import { assertEquals } from "jsr:@std/assert@1";
import { mergeTree } from "../connectors/devto/connector.ts";
import { flattenTree, ParsedComment } from "../connectors/devto/parse.ts";
import { richerContext } from "./store.ts";
import { carriedGist, draftLength } from "./draft_run.ts";

const FULL = "I understand the wish to find a number for a developer's work, and I agree velocity is the wrong one. The signal I trust most is how long it takes a new person to make a safe change.";

const phone: ParsedComment = {
  id_code: "3hel2", kind: "reply", text: "That last point is probably the best answer.", url: "https://dev.to/d/comment/3hel2", created_at: "2026-10-12T06:20:59Z",
  author: { username: "dimitris" },
  article: { id: "4816099", title: "Shipping faster with AI", url: "https://dev.to/d/shipping", author_username: null, text: null },
  parent: { id_code: "3h2e9", text: "I understand the wish to find a number for a developer's work, and I agree ve...", author_username: "yahhi" },
};

Deno.test("mergeTree: the tree's full thread and article body replace the phone's cut ones", () => {
  const tree = flattenTree({ id: 4816099, title: "Shipping faster with AI", url: "https://dev.to/d/shipping", body_markdown: "The article body.", user: { username: "dimitris" } }, "yahhi", [
    { id_code: "3h2e9", created_at: "2026-10-11T00:00:00Z", body_html: `<p>${FULL}</p>`, user: { username: "yahhi" },
      children: [{ id_code: "3hel2", created_at: "2026-10-12T06:20:59Z", body_html: "<p>That last point is probably the best answer.</p>", user: { username: "dimitris" } }] },
  ]);
  const m = mergeTree(phone, tree.find((c) => c.id_code === "3hel2"), { id: 4816099, title: "", url: "", comments_count: 2, published_at: "" });
  assertEquals(m.thread?.[0].text, FULL);
  assertEquals(m.parent?.text, FULL);
  assertEquals(m.article.text, "The article body.");
  assertEquals(m.article.author_username, "dimitris");
  assertEquals(m.under_owner, true);
  assertEquals(mergeTree(phone, undefined, null), phone);
});

Deno.test("richerContext: a longer thread or post body replaces the stored one, a shorter one doesn't", () => {
  const cut = [{ author: "yahhi", text: "I understand… ve..." }];
  const full = [{ author: "yahhi", text: FULL }];
  assertEquals(richerContext({ thread: cut, my_post: { title: "t", text: "" } }, { thread: full, my_post: { title: "t", text: "body" } }),
    { thread: full, my_post: { title: "t", text: "body" } });
  assertEquals(richerContext({ thread: full, my_post: { text: "body" } }, { thread: cut, my_post: { text: "" } }), null);
});

Deno.test("draftLength: asked → previous version's → triage route", () => {
  assertEquals(draftLength("full", "one_line", "short_draft"), "full");
  assertEquals(draftLength(null, "one_line", "draft"), "one_line");
  assertEquals(draftLength(undefined, undefined, "short_draft"), "one_line");
  assertEquals(draftLength(undefined, null, "draft"), "full");
});

Deno.test("carriedGist: a new point wins; otherwise the previous version's point is kept", () => {
  assertEquals(carriedGist("  my point ", { gist: "old" }), { gist: "my point", newGist: "my point" });
  assertEquals(carriedGist(null, { length: "one_line", gist: "old point" }), { gist: "old point", newGist: null });
  assertEquals(carriedGist("", { gist: "old point" }), { gist: "old point", newGist: null });
  assertEquals(carriedGist(undefined, null), { gist: null, newGist: null });
  assertEquals(carriedGist(undefined, { gist: 42 }), { gist: null, newGist: null });
});

Deno.test("hiddenIn: comments she hid come back as [hidden by post author] with no user; flattenTree drops them", async () => {
  const { hiddenIn, flattenTree } = await import("../connectors/devto/parse.ts");
  const tree = [
    { id_code: "3h553", created_at: "2026-10-10T05:20:36Z", body_html: "<p>[hidden by post author]</p>", user: {}, children: [] },
    { id_code: "aa1", created_at: "2026-10-10T05:21:00Z", body_html: "<p>Real comment</p>", user: { username: "dimitris" },
      children: [{ id_code: "aa2", created_at: "2026-10-10T05:22:00Z", body_html: "<p>[hidden by post author]</p>", user: {}, children: [] }] },
  ];
  assertEquals(hiddenIn(tree), ["3h553", "aa2"]);
  assertEquals(flattenTree({ id: 1, title: "t", url: "u", user: { username: "yahhi" } }, "yahhi", tree).map((c) => c.id_code), ["aa1"]);
});
