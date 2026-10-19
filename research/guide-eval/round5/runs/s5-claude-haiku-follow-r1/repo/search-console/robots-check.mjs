// Checks site/robots.txt the way Google does: the longest matching rule wins,
// and on a tie Allow wins. Supports * and a trailing $. Python's urllib.robotparser
// applies first-match, so it is not used here.
// Usage: node search-console/robots-check.mjs [robots.txt path]
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const file = process.argv[2] ?? join(here, "..", "site", "robots.txt");

function parse(text) {
  const rules = [];
  let applies = false;
  for (const raw of text.split("\n")) {
    const line = raw.replace(/#.*/, "").trim();
    const m = line.match(/^([A-Za-z-]+):\s*(.*)$/);
    if (!m) continue;
    const [, key, value] = m;
    if (key.toLowerCase() === "user-agent") applies = value === "*";
    else if (applies && /^(allow|disallow)$/i.test(key) && value) {
      rules.push({ type: key.toLowerCase(), pattern: value });
    }
  }
  return rules;
}

function toRegex(pattern) {
  const body = pattern
    .replace(/\$$/, "")
    .split("*")
    .map(s => s.replace(/[.+?^${}()|[\]\\]/g, "\\$&"))
    .join(".*");
  return new RegExp("^" + body + (pattern.endsWith("$") ? "$" : ""));
}

function allowed(rules, path) {
  let best = null;
  for (const rule of rules) {
    if (!toRegex(rule.pattern).test(path)) continue;
    const len = rule.pattern.length;
    if (!best || len > best.len || (len === best.len && rule.type === "allow")) {
      best = { len, type: rule.type, pattern: rule.pattern };
    }
  }
  return { ok: !best || best.type === "allow", by: best };
}

const rules = parse(readFileSync(file, "utf8"));

// [path, expected] — expected true means Googlebot may fetch it.
const cases = [
  // Pages and the data they render from: must be allowed.
  ["/n/drip-line-pressure", true],
  ["/", true],
  ["/skills", true],
  ["/v1/notes/drip-line-pressure", true],
  ["/v1/notes/soil-ph-kit-review", true],
  ["/v1/notes?limit=50", true],
  // Blocked: POST-only or per-user, and admin.
  ["/v1/notes/drip-line-pressure/reactions", false],
  ["/v1/me", false],
  ["/v1/me/drafts", false],
  ["/v1/auth/token", false],
  ["/admin/", false],
  ["/admin/users", false],
];

let failed = 0;
for (const [path, expected] of cases) {
  const { ok, by } = allowed(rules, path);
  const pass = ok === expected;
  if (!pass) failed++;
  const why = by ? `${by.type} ${by.pattern}` : "no rule";
  console.log(`${pass ? "PASS" : "FAIL"}  ${ok ? "allow" : "block"}  ${path}  (${why})`);
}
console.log(failed ? `${failed} case(s) failed` : `all ${cases.length} cases passed`);
process.exit(failed ? 1 : 0);
