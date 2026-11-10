# Effect 4 Migration and Implementation Notes

## Which parts of the colleague's note applied

1. **`effect` package version and imports (`effect` 4.x / `effect/http`)**:
   - The colleague's note pointed out that in Effect 4, HTTP client functionality resides in `effect/http` directly within the `effect` package (version 4.1.2), rather than the obsolete `@effect/platform` v3 package. This applied directly.

2. **In-package agent docs (`node_modules/effect/ai-docs/`)**:
   - Specifically, `ai-docs/src/50_http-client/10_basics.ts` served as a direct template for structuring the `Context.Service`, configuring `HttpClient.HttpClient`, applying request preprocessing (`HttpClientRequest.prependUrl`, `HttpClientRequest.acceptJson`), filtering status with `HttpClient.filterStatusOk`, and using `FetchHttpClient.layer`.

3. **Effect 4 API naming conventions**:
   - `Context.Service` for defining the service tag and interface.
   - `Schema.TaggedError` for defining custom tagged errors.
   - `Config.String` for reading configuration from environment variables.
   - `HttpClient.retryTransient` with `Schedule.exponential(50)` and `times: 3` for retrying network errors and 5xx responses with exponential backoff starting at 50 ms.

4. **Schema validation with `HttpClientResponse.schemaBodyJson`**:
   - Response validation uses `HttpClientResponse.schemaBodyJson(RatesResponse)` with `Schema.Struct({ base: Schema.String, date: Schema.String, rates: Schema.Record(Schema.String, Schema.Number) })`. Invalid response formats and schema mismatches trigger `InvalidResponseError`, mapped to exit code 2.

## What did not apply or differed

- **`@effect/platform-node` / `NodeRuntime.runMain`**: The colleague's note mentioned runtime runners from `@effect/platform-node`. Because we must not depend on legacy `@effect/platform` packages and need precise control over process exit codes (0, 1, 2, 3) as well as specific stdout/stderr formatting, execution is handled using `Effect.runPromiseExit` and `Exit.match` with `process.exit`.
