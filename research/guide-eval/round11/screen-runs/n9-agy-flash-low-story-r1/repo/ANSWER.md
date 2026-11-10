# Colleague's Note: What Applied and What Was Ignored

## Summary of Applied Parts

1. **Package installation and imports**:
   - Installed `effect@latest` (`effect@4.1.2`).
   - Did not install `@effect/platform` (as noted, in Effect 4 the HTTP client is built into `effect/http`).
   - Consulted `node_modules/effect/AGENTS.md` and `node_modules/effect/ai-docs/src/50_http-client/10_basics.ts` for idiomatic Effect 4 patterns.

2. **Effect 4 API Names**:
   - `Context.Service`: Used `class RatesService extends Context.Service<RatesService, ...>()("app/RatesService")` with a static layer rather than `Context.Tag`.
   - `effect/http`: Used `FetchHttpClient`, `HttpClient`, `HttpClientResponse`, and `HttpClientError` from `effect/http`.
   - `Config.String`: Used `Config.String("RATES_URL")` to read configuration from environment variables.
   - `Schema.TaggedError`: Defined custom errors using `Schema.TaggedError`.
   - `HttpClient.retryTransient` with `Schedule.exponential(50)`: Configured retries for transient failures (network errors and 5xx responses) with exponential backoff starting at 50 ms and `times: 3`.
   - `HttpClientResponse.schemaBodyJson`: Used `HttpClientResponse.schemaBodyJson(RatesResponse)` to parse and validate the JSON response body against the schema.

## Parts Ignored or Adjusted

1. **`NodeRuntime.runMain`**:
   - The note mentioned `NodeRuntime.runMain` from `@effect/platform-node` or `ai-docs/src/01_effect/06_running/10_run-main.ts`. Because the requirement specifies no `@effect/platform` dependencies, and specific stderr output / exit codes (0, 1, 2, 3) must be strictly controlled, the entry point uses `Effect.runPromise` with `Effect.matchCauseEffect` and `process.exit(code)` / `Console.log` / `Console.error`.
2. **Schema Definition**:
   - In Effect 4, `Schema.Record` takes two arguments: `Schema.Record(Schema.String, Schema.Number)` (rather than `{ [code: string]: number }` as an object argument).
