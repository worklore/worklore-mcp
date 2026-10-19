// Checks robots.txt rules the way Googlebot does: the longest matching rule wins,
// and Allow wins a tie. Only the `User-agent: *` group is read.
// Usage: node scripts/check-robots.mjs site/robots.txt
import { readFileSync } from "node:fs";

const file = process.argv[2];
if (!file) {
  console.error("usage: node scripts/check-robots.mjs <robots.txt>");
  process.exit(2);
}

// Paths the site needs crawled, and paths that must stay out of the index.
// `want` is "allow" or "block". Paths are what Googlebot requests, including query strings.
const cases = [
  // Pages a crawler opens.
  ["/", "allow"],
  ["/n/drip-line-pressure", "allow"],
  // Data the note page and home list fetch while rendering. Blocking these causes soft 404s.
  ["/v1/notes", "allow"],
  ["/v1/notes?limit=50", "allow"],
  ["/v1/notes/drip-line-pressure", "allow"],
  // Crawler traps and per-user / auth endpoints that must stay blocked.
  ["/v1/notes/drip-line-pressure/reactions", "block"],
  ["/v1/me", "block"],
  ["/v1/me/drafts", "block"],
  ["/v1/auth/token", "block"],
  ["/admin/", "block"],
];

function parseGroup(text) {
  const rules = [];
  let inStar = false;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.replace(/#.*/, "").trim();
    if (!line) continue;
    const idx = line.indexOf(":");
    if (idx < 0) continue;
    const field = line.slice(0, idx).trim().toLowerCase();
    const value = line.slice(idx + 1).trim();
    if (field === "user-agent") {
      inStar = value === "*";
    } else if (inStar && (field === "allow" || field === "disallow")) {
      // An empty Disallow means "allow everything", so it never matches anything.
      if (value === "") continue;
      rules.push({ type: field, pattern: value });
    }
  }
  return rules;
}

function toRegExp(pattern) {
  const anchored = pattern.endsWith("$");
  const body = anchored ? pattern.slice(0, -1) : pattern;
  const source = body
    .split("*")
    .map(s => s.replace(/[.+?^${}()|[\]\\]/g, "\\$&"))
    .join(".*");
  return new RegExp("^" + source + (anchored ? "$" : ""));
}

function decide(rules, path) {
  let best = null;
  for (const rule of rules) {
    if (!toRegExp(rule.pattern).test(path)) continue;
    const len = rule.pattern.replace(/\$$/, "").length;
    if (!best || len > best.len || (len === best.len && rule.type === "allow")) {
      best = { ...rule, len };
    }
  }
  if (!best) return { verdict: "allow", by: "no matching rule" };
  return { verdict: best.type === "allow" ? "allow" : "block", by: `${best.type}: ${best.pattern}` };
}

const rules = parseGroup(readFileSync(file, "utf8"));
let failures = 0;
for (const [path, want] of cases) {
  const { verdict, by } = decide(rules, path);
  const ok = (verdict === "allow") === (want === "allow");
  if (!ok) failures++;
  console.log(`${ok ? "ok  " : "FAIL"} ${verdict.padEnd(5)} ${path.padEnd(42)} (${by})`);
}
console.log(failures ? `\n${failures} case(s) failed` : "\nall cases pass");
process.exit(failures ? 1 : 0);
