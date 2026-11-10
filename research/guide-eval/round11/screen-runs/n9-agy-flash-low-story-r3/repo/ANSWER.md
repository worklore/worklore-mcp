# Note on Effect 4 Migration and Applied Findings

This document summarizes which parts of the colleague's migration note applied to the rewrite of `src/main.ts` with Effect.

## Parts That Applied

1. **Package and Versioning**:
   - Installed `effect@latest` (v4.1.2) directly.
   - Did not install `@effect/platform` (which was still at 0.97.2 from Effect v3).

2. **HTTP Client in `effect/http`**:
   - As noted, Effect 4 bundles the HTTP client inside `effect/http` (`FetchHttpClient`, `HttpClient`, `HttpClientRequest`, `HttpClientResponse`).

3. **In-Package Documentation**:
   - Consulted `node_modules/effect/ai-docs/src/50_http-client/10_basics.ts` for configuring the `HttpClient` service, `FetchHttpClient.layer`, `HttpClientRequest.prependUrl`, and `HttpClientResponse.schemaBodyJson`.

4. **Effect 4 API Names**:
   - `Context.Service` was used to define the `RatesService` service tag and interface (instead of v3 `Context.Tag`).
   - `Schema.TaggedError` was used to define typed error classes (`UnknownCurrencyError`, `InvalidResponseError`, `RatesError`).
   - `Config.String` was used for reading environment configuration (`RATES_URL`) instead of v3 `Config.string`.
   - `HttpClient.retryTransient` with `Schedule.exponential(50)` was used to retry network errors and 5xx responses up to 3 times.

## Parts That Did Not Apply or Required Adjustments

1. **Response Validation Error Handling**:
   - `HttpClientResponse.schemaBodyJson` fails with `Schema.SchemaError` for schema validation failures, or `HttpClientError` with reason `DecodeError` for non-JSON responses. Both were mapped to `InvalidResponseError` to exit with code 2 (`invalid response`).
2. **Runtime Execution**:
   - Rather than relying on `NodeRuntime` (which was part of `@effect/platform-node` in v3), the CLI program runs directly via `Effect.runPromise` and sets `process.exitCode` according to the requirement specification.
3. **Catch Combinators in Effect 4**:
   - In Effect 4, catch-all combinators are `Effect.catch` and `Effect.catchDefect` (as opposed to v3's `Effect.catchAll` / `Effect.catchAllDefect`).
