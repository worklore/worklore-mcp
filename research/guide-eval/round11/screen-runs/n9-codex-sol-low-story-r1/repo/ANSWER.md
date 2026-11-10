# Effect CLI rewrite

The colleague's note applied to the Effect 4 API names and package layout: this project uses `effect@4.1.2`, `Context.Service`, the HTTP client from `effect/http`, `HttpClient.retryTransient`, and `Schedule.exponential`. I used the package's `AGENTS.md` and HTTP client example to confirm those APIs. The note's `Schema.TaggedError` and `Config.String` details were not needed; this CLI uses ordinary error classes and reads `RATES_URL` in the service layer. I did not install `@effect/platform`.

Verified with `npx tsc --noEmit` and a local HTTP server covering success, unknown currency, invalid response, and recovery after two HTTP 503 responses.
