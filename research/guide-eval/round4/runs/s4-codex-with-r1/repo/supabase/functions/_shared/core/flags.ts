// Which connectors are on. Env CONNECTORS = comma list (function secret);
// default "devto": Bluesky stays in the code but is off until the owner turns
// it on (docs/ARCHITECTURE.md).

export const DEFAULT_CONNECTORS = ["devto"];

export function enabledConnectorIds(raw = Deno.env.get("CONNECTORS")): string[] {
  const s = (raw ?? "").trim();
  if (!s) return DEFAULT_CONNECTORS;
  return s.split(",").map((x) => x.trim().toLowerCase()).filter(Boolean);
}

export const isEnabled = (id: string) => enabledConnectorIds().includes(id);
