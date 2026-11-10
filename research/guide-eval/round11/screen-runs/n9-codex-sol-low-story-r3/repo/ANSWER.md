# Effect CLI rewrite

Installed `effect@4.1.2` from npm and rewrote the CLI around a `Rates` service and layer. It uses Effect's fetch HTTP client, validates the JSON body with Schema, and retries transient request failures up to three times with exponential backoff starting at 50 ms.

The colleague's note applied to the Effect 4 API names (`Context.Service`, `Schema.TaggedError`, and `effect/http`), the bundled `node_modules/effect/AGENTS.md` and HTTP client example, and `HttpClient.retryTransient` with `Schedule.exponential`. `Config.String` was not needed because this CLI reads `RATES_URL` directly from its environment. No `@effect/platform` package was installed.

Verified with `npx tsc --noEmit` and a local HTTP server: success, unknown currency, invalid response, 404 failure, and a 503 response that succeeds after three retries.
