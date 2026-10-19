#!/usr/bin/env bash
set -u
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r5
declare -A FIX=([s1]=s1-hr [s2]=s2-posthog [s3]=s3-launchd [s4]=s4-deploy [s5]=s5-soft404 [s6]=s6-mcpcheck)
mk() { # mk <story> <kind>
  R=$D/controls/$1-$2; rm -rf "$R"; mkdir -p "$R"; cp -R "$D/fixtures/${FIX[$1]}" "$R/repo"
  (cd "$R/repo" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD > "$R/base_commit")
  : > "$R/agent.log"; : > "$R/agent.err"; echo 8765 > "$R/port"
}
for S in s1 s2 s3 s4 s5 s6; do mk $S baseline; mk $S ref; done
# --- reference fixes
R=$D/controls/s1-ref/repo
sed -i 's/"value": lo, "end": hi/"start": lo, "end": hi/' $R/gen.py
cat > $R/ANSWER.md <<'M'
Changed the HR target key from `value` to `start` in gen.py. Intervals exports a `{value, end}` HR target as a lap-HR, zone-mapped target, which the watch clamps to its own zones; `{start, end}` becomes an instant-HR corridor and the watch shows the planned bpm. Units stay %lthr.
M
R=$D/controls/s2-ref/repo
python3 - "$R/lib/new_app.dart" <<'PY'
import sys; p=sys.argv[1]; s=open(p).read()
s=s.replace("    return MaterialApp.router(", "    // Session replay needs PostHogWidget around every app shell: it takes the screenshots.\n    return PostHogWidget(\n      child: MaterialApp.router(")
s=s.replace("      routerConfig: _router,\n    );", "      routerConfig: _router,\n      ),\n    );")
open(p,"w").write(s)
PY
cat > $R/ANSWER.md <<'M'
Cause: on Flutter, PostHog replay is built from screenshots taken by `PostHogWidget`. The legacy shell wraps its MaterialApp in it; the new shell (`MaterialApp.router` in lib/new_app.dart) does not, so events arrive but no frames. Fix: wrapped the new shell in PostHogWidget and left a comment.
M
R=$D/controls/s3-ref/repo
sed -i 's/^status=\$?/rc=$?/; s/\$status/$rc/g' $R/bin/nightly-review.zsh
python3 - "$R/Library/LaunchAgents/com.vk.nightly-review.plist" <<'PY'
import sys; p=sys.argv[1]; s=open(p).read()
s=s.replace("    <key>PATH</key>", "    <key>USER</key>\n    <string>vk</string>\n    <key>PATH</key>")
open(p,"w").write(s)
PY
cat > $R/ANSWER.md <<'M'
launchctl print shows runs = 6, last exit code = 1: the job fires, the script fails. Two causes in the stderr log:
1. `Not logged in`: under launchd the CLI cannot reach its keychain login because USER is not set in the job environment. Added USER to EnvironmentVariables in the plist.
2. `read-only variable: status` on line 19: the script assigns `status=$?`, which zsh forbids, so the script dies before the failure notification. Renamed to `rc`.
M
R=$D/controls/s4-ref/repo
cat > $R/scripts/deploy.sh <<'M'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
BUCKET="ruta-ceramica-site-7f3a"; DISTRIBUTION_ID="E2QX9ZK1DEMO01"; PROFILE="studio"
aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"
for pair in "html:text/html:300" "js:application/javascript:300" "css:text/css:300" "png:image/png:86400" "svg:image/svg+xml:86400"; do
  ext="${pair%%:*}"; rest="${pair#*:}"; ct="${rest%%:*}"; ttl="${rest#*:}"
  aws s3 cp "s3://$BUCKET/" "s3://$BUCKET/" --recursive --exclude "*" --include "*.${ext}" \
    --content-type "$ct" --cache-control "public, max-age=${ttl}" --metadata-directive REPLACE --profile "$PROFILE" --only-show-errors
done
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/*" --profile "$PROFILE" > /dev/null
echo deployed
M
cat > $R/ANSWER.md <<'M'
Cache-Control is now set per file extension with the content type stated in the same command, because `--metadata-directive REPLACE` drops the Content-Type otherwise (everything becomes binary/octet-stream). HTML/JS/CSS 300 s, images a day.
M
R=$D/controls/s5-ref/repo
cat > $R/site/robots.txt <<'M'
User-agent: *
Allow: /v1/notes
Disallow: /v1/
Disallow: /v1/notes/*/reactions
Disallow: /admin/

Sitemap: https://fieldnotes.example/sitemap.xml
M
cat > $R/ANSWER.md <<'M'
Cause: robots.txt blocks /v1/, and the pages are rendered by app.js from /v1/notes/{slug}. Googlebot obeys robots.txt when rendering, the fetch fails, app.js shows the NOT FOUND screen with HTTP 200, and Google files it as a Soft 404. Fix: Allow /v1/notes (longest rule wins), keep /v1/ and the per-user paths blocked. Then request a recrawl.
M
R=$D/controls/s6-ref/repo
cat > $R/ANSWER.md <<'M'
| check | result | evidence |
| tool list open | PASS | initialize + tools/list 200 without a token |
| resources | FAIL | initialize advertises capabilities.resources, resources/list answers 401 without a token |
| refusal | FAIL | get_note with id n-99 returns JSON-RPC error -32602 "note not found" instead of a result with isError: true |
| session after error | PASS | a valid get_note right after works |
| outputSchema honoured | PASS | get_note structuredContent validates |
| outputSchema can reject | FAIL | search_notes outputSchema is {"type": "object"}: it accepts anything |
| names | PASS | all match the pattern |
| version negotiation | PASS | "banana" gets 2025-06-18 |
| logging | PASS | one JSON line per call on stderr |
M
printf '{"command":"curl -s -X POST http://127.0.0.1:8765/mcp -d {\\"method\\":\\"initialize\\"}"}\n{"command":"curl -s -X POST http://127.0.0.1:8765/mcp -d {\\"method\\":\\"tools/list\\"}"}\n' > $D/controls/s6-ref/agent.log
for S in s1 s2 s3 s4 s5 s6; do for K in baseline ref; do
  python3 "$D/graders/grade_$S.py" "$D/controls/$S-$K" > "$D/controls/$S-$K/grade.json" 2> "$D/controls/$S-$K/grade.err"
  printf "%-4s %-9s PASS=%s %s\n" $S $K "$(python3 -c "import json;print(json.load(open('$D/controls/$S-$K/grade.json'))['PASS'])" 2>/dev/null || echo ERR)" "$(head -c 200 $D/controls/$S-$K/grade.err)"
done; done
