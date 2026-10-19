// The built-in connectors. Every Edge Function imports this once, so the
// core's registry knows them. Adding a network = a folder here + one line.
// GitHub is a source connector (the project's `hearback/` folder; issues later).

import { registerConnector } from "../core/registry.ts";
import { blueskyConnector } from "./bluesky/connector.ts";
import { devtoConnector } from "./devto/connector.ts";
import { githubConnector } from "./github/connector.ts";

registerConnector(devtoConnector);
registerConnector(blueskyConnector);
registerConnector(githubConnector);
