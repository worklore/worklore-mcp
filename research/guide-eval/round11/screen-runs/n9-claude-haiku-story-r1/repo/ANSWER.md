# fx-cli on Effect 4

`src/main.ts` is rewritten with Effect 4.1.2, the current `effect` on npm.
`npx tsc --noEmit` passes. `@effect/platform` and `@effect/platform-node` are not installed.

## What was built

- **`Rates` service** (`Context.Service`) with a `Rates.layer`. The layer reads
  `RATES_URL` with `Config.String` and uses `effect/http` (`FetchHttpClient.layer`).
- **Response validation** with `Schema.Struct`: `base`, `date`, and
  `rates: Schema.Record(Schema.String, Schema.Number)`.
- **Retries**: network errors and 5xx responses are retried up to 3 times with
  `Schedule.exponential(50)` (waits of 50, 100, 200 ms). Other failures are not retried.
- **Errors** are `Schema.TaggedError` classes, mapped to exit codes in one place:
  `UnknownCurrency` → 1, `InvalidResponse` → 2, `RatesUnavailable` and `UsageError` → 3.
- The program runs with `Effect.runPromise` and sets `process.exitCode`. Nothing needs `NodeRuntime`.

## Colleague's note: what applied

- **Applied: use the current v4 package.** `npm view effect version` returns `4.1.2`.
  I installed `effect@latest`. The note's "2026-10-01 stable" date was not checked.
- **Applied: v4 names.** `Context.Service`, `Schema.TaggedError`, `Config.String`,
  `effect/http`, and `Effect.fn` all compile against 4.1.2 as used here.
- **Applied: no `@effect/platform`.** `npm ls` shows only `effect@4.1.2`.
- **Applied: read the bundled docs first.** I read `node_modules/effect/AGENTS.md` and
  `ai-docs/src/50_http-client/10_basics.ts`, and used the service and layer shape from it.
- **Applied: `npx tsc --noEmit` early and often.** It was the source of every API fix.
- **Partly applied: retries.** I did not use `HttpClient.retryTransient`. Its built-in
  transient check also retries 429 and 408, and the spec asks for network errors and 5xx
  only. I used `Effect.retry` with the same `Schedule.exponential` and a predicate
  restricted to those cases.
- **Not applied: `NodeRuntime.runMain`.** It belongs to `@effect/platform-node`, which
  this CLI does not need.
- **Applied: ground rules.** Nothing was published, deployed, or sent anywhere. All work
  stayed in this directory.

## Decisions you may want to change

- **Missing arguments** print the usage line and exit 3. The spec's "any other failure"
  rule covers this, but a conventional CLI would use a different code.
- **Missing `RATES_URL`** prints `error: ...` and exits 3.
- **Body read failures** after a successful response (including a dropped connection
  mid-body) are reported as `invalid response`, exit 2.
- **Rate lookup** uses `Object.hasOwn`. `USD constructor` reports `unknown currency`
  rather than returning the prototype property.
- **The base code** is passed to the URL with `encodeURIComponent` and is not uppercased.

## Verification

A local test server (outside the repo) served each case. Results from this run:

| Case | Result |
| --- | --- |
| success `USD EUR` | stdout `1 USD = 0.9214 EUR`, exit 0 |
| `USD XYZ` | stderr `unknown currency: XYZ`, exit 1 |
| non-JSON body, missing `rates`, non-numeric rate | stderr `invalid response`, exit 2 |
| 503, 503, then 200 | succeeds, exit 0, 3 requests |
| 500 every time | exit 3, 4 requests (1 + 3 retries), about 350 ms of backoff |
| 404 | exit 3, 1 request (not retried) |
| network refused | exit 3 |
| `RATES_URL` unset | exit 3, clean message |
| missing arguments | usage on stderr, exit 3 |

Not run: a test with a real rates service. No commit was made.
