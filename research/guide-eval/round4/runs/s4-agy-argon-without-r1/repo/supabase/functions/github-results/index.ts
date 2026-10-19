// POST /functions/v1/github-results  {}
// Cron every 20 min (service role): re-reads the issues ideas turned into;
// one that is done (closed as completed, or Done on the linked board) gets
// its result stored and a follow-up draft for everyone who asked. Never
// posts. docs/API.md › github-results

import "../_shared/connectors/mod.ts";
import { caller } from "../_shared/server/ctx.ts";
import { sweep } from "../_shared/server/github_results.ts";
import { HttpError, serve } from "../_shared/server/http.ts";

serve(async (req) => {
  const c = await caller(req);
  if (c.kind !== "service") throw new HttpError(403, "forbidden", "Only the scheduler runs this.");
  return await sweep();
});
