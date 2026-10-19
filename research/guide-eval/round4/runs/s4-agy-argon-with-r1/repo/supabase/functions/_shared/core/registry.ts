// Connectors register themselves here (connectors/mod.ts); the core asks the
// registry for platform facts and never imports a connector.

import type { Connector } from "./types.ts";

const registry = new Map<string, Connector>();

export function registerConnector(c: Connector): void {
  registry.set(c.id, c);
}

export function unregisterConnector(id: string): void {
  registry.delete(id);
}

export function connector(id: string): Connector | undefined {
  return registry.get(id);
}

export function connectors(): Connector[] {
  return [...registry.values()];
}

/** Reply length limit for a platform (graphemes), or null. */
export function replyLimit(platform: string): number | null {
  return registry.get(platform)?.reply.maxGraphemes ?? null;
}
