// POST /functions/v1/poll-bluesky  {project_id?}
// The Bluesky connector's worker. Bluesky is OFF by default (env CONNECTORS),
// its cron job is unscheduled; while off this answers {disabled: true}.
// docs/API.md › poll-bluesky

import "../_shared/connectors/mod.ts";
import { pollConnector } from "../_shared/core/worker.ts";
import { serve } from "../_shared/server/http.ts";

serve((req, body) => pollConnector("bluesky", req, body));
