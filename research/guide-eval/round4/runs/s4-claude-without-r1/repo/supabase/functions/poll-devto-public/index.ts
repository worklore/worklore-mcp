// POST /functions/v1/poll-devto-public  {project_id?}
// The dev.to connector's worker (cron every 15 min with the service role: all
// active dev.to accounts; a founder: her project's accounts). Rate rules are
// the connector's (connectors/devto). New items are triaged while time allows;
// the rest are picked up by the triage-pending cron. docs/API.md › poll-devto-public

import "../_shared/connectors/mod.ts";
import { pollConnector } from "../_shared/core/worker.ts";
import { serve } from "../_shared/server/http.ts";

serve((req, body) => pollConnector("devto", req, body));
