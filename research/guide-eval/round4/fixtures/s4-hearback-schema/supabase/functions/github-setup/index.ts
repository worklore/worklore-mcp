// GET /functions/v1/github-setup?installation_id=…&setup_action=install|update|request&state=…
// The GitHub App's Setup URL (public: verify_jwt is off, GitHub's redirect
// carries no Supabase session; the one-time state is the authentication).
// Stores the installation and its repos, links it to the state's project,
// then redirects: the app's dev.hearback.app://github-installed?ok=1 on
// success from the phone, otherwise the static page
// https://hearback.dev/github-installed.html?ok=…&reason=… (Supabase serves
// function HTML as plain text, so the page lives on the site).
// docs/API.md › github-setup, install.ts for the rules.

import { githubApp } from "../_shared/connectors/github/app.ts";
import { handleSetup, setupRedirect, SetupOutcome } from "../_shared/connectors/github/install.ts";
import { installGithub, supabaseInstallStore } from "../_shared/server/github.ts";

const redirect = (to: string) => new Response(null, { status: 302, headers: { location: to, "cache-control": "no-store", "referrer-policy": "no-referrer" } });

Deno.serve(async (req) => {
  if (req.method !== "GET") return new Response("GET only", { status: 405 });
  const params = new URL(req.url).searchParams;
  let outcome: SetupOutcome;
  const app = githubApp();
  if (!app) {
    console.error("github-setup: GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY not set");
    outcome = { ok: false, client: null, reason: "github_error" };
  } else {
    try {
      outcome = await handleSetup(params, supabaseInstallStore(), installGithub(app));
    } catch (e) {
      console.error("github-setup failed:", (e as Error).message.slice(0, 200));
      outcome = { ok: false, client: null, reason: "github_error" };
    }
  }
  console.log("github-setup:", JSON.stringify(outcome.ok
    ? { ok: true, installation_id: outcome.installation_id, repos: outcome.repos, refreshed_only: outcome.refreshed_only }
    : { ok: false, reason: outcome.reason }));
  return redirect(setupRedirect(outcome));
});
