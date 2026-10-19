---

# Badges for your users' achievements — a self-updating SVG for any app

You know the little colored pills on GitHub READMEs — `build: passing`,
`coverage: 98%`? That format is a tiny, perfect growth loop, and it works for
*any* app that keeps a public stat per item. My site gives each developer story
a count of how many times a real person's agent reproduced it. That number is
the whole point — but it was trapped on my site. I wanted authors to be able to
paste their proof onto their GitHub profile, where it does two jobs at once:
shows off *their* achievement, and quietly links back to *my* site.

So I built an embeddable, self-updating SVG badge — one for a single item, one
that sums an author's whole profile. The nice surprise: **it needs no auth at
all.** A badge has to be public to embed anywhere, and I only ever put already-
public numbers in it — so "no login" isn't a shortcut, it's the feature. That's
what lets a user drop it in a README and lets that README render it for
everyone.

Two things bit me, and they're the whole craft of this:

- **Don't put a real ✓ (or ★, or ×) as a text glyph.** It renders fine for you
  and shows up as a tofu box `□` for anyone whose renderer lacks that font
  glyph. I drew the checkmark as an inline SVG `<path>` instead — guaranteed
  everywhere.
- **GitHub proxies and caches your image** (its "camo" layer). The count is
  live at the source, but on a README it refreshes within the cache window, not
  instantly — so send a sane `Cache-Control` and don't promise real-time.

The result: every item and every author now has a badge. I surfaced a
click-to-copy version inside the app too, but the embed is just markdown, so it
works anywhere markdown does. The badges are already on my own repo's README,
doing their little double duty.

## Reproduce this
Prerequisites: a web app/API you control that stores a public, per-item stat
(reproductions, stars, downloads, streak — anything already public), and a way
to add a public HTTP route.

Your agent will need from you: which stat to surface, where it lives (your DB/
store), your brand colors, and your public base URL.

Steps:
1. Add a **public** `GET /badge/{id}.svg` route that looks up the item's stat.
   No auth — the badge must be embeddable by anyone; only expose already-public
   numbers.
2. Return a two-segment "shields-style" SVG: a dark label segment (your app
   name) + a colored value segment (the stat). Compute each segment's width from
   its text length so it never clips. Set `Content-Type: image/svg+xml`.
3. Draw any icon (✓, ★) as an inline `<path>`, never a unicode character — text
   glyphs depend on the viewer's fonts and show as boxes in some renderers. Keep
   the SVG fully self-contained (no external fonts or images).
4. Add a short `Cache-Control` (e.g. `public, max-age=300`). GitHub's image
   proxy will cache it regardless; this just keeps the source cheap.
5. Hand users the embed line — the trailing link is the backlink that promotes
   your app:
   `[![yourapp](https://yourapp.com/badge/{id}.svg)](https://yourapp.com/item/{id})`
6. Optional: show the same embed as click-to-copy in your app's UI so users find
   it without reading docs.

Verify: paste the badge into a GitHub README. It must render as a crisp badge —
not a broken-image icon, and no `□` where the icon should be. Confirm the number
matches your app. Then bump the item's stat and confirm the badge updates after
GitHub's cache window (a README edit busts it immediately).

Caveat to state up front: because of GitHub's camo cache, treat the count as
"eventually fresh," not real-time — and keep the SVG self-contained, or camo
will render a broken image.
