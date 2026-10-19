// The key two project URLs are "the same" by: scheme and host lowercased,
// "www." stripped, trailing slashes and the fragment dropped; path and query
// kept. Same rule as SQL hb_url_key() (migration 20261009150000) and the
// app's normalizeProjectUrl. Pure; tested.

export function urlKey(url: string | null | undefined): string | null {
  let u = (url ?? "").trim();
  if (!u) return null;
  if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(u)) u = `https://${u}`;
  const m = u.match(/^([a-zA-Z][a-zA-Z0-9+.-]*):\/\/([^/?#]+)(.*)$/);
  if (!m) return u.replace(/\/+$/, "").toLowerCase();
  const rest = m[3].replace(/#.*$/, "").replace(/\/+$/, "");
  return `${m[1].toLowerCase()}://${m[2].toLowerCase().replace(/^www\./, "")}${rest}`;
}
