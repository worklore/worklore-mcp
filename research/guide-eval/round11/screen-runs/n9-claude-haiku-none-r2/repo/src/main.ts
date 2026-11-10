import { Console, Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientResponse } from "effect/http"
import * as HttpClientError from "effect/http/HttpClientError"

// ---------------------------------------------------------------------------
// Response shape
// ---------------------------------------------------------------------------

const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
export type RatesResponse = typeof RatesResponse.Type

// ---------------------------------------------------------------------------
// Errors (each maps to an exit code in `main` below)
// ---------------------------------------------------------------------------

export class UsageError extends Schema.TaggedError<UsageError>()("UsageError", {
  message: Schema.String
}) {}

export class RatesRequestError extends Schema.TaggedError<RatesRequestError>()("RatesRequestError", {
  cause: Schema.Defect()
}) {}

export class InvalidResponseError extends Schema.TaggedError<InvalidResponseError>()("InvalidResponseError", {}) {}

export class UnknownCurrencyError extends Schema.TaggedError<UnknownCurrencyError>()("UnknownCurrencyError", {
  currency: Schema.String
}) {}

// ---------------------------------------------------------------------------
// Rates service
// ---------------------------------------------------------------------------

export class RatesApi extends Context.Service<RatesApi, {
  readonly latest: (base: string) => Effect.Effect<RatesResponse, RatesRequestError | InvalidResponseError>
}>()("app/RatesApi") {
  static readonly layer = Layer.effect(
    RatesApi,
    Effect.gen(function*() {
      const baseUrl = process.env.RATES_URL
      if (baseUrl === undefined || baseUrl === "") {
        return yield* new UsageError({ message: "RATES_URL is not set" })
      }

      // Non-2xx responses become StatusCodeError; network failures are
      // TransportError. Retry only those two kinds, and only 5xx statuses.
      const client = (yield* HttpClient.HttpClient).pipe(
        HttpClient.filterStatusOk,
        HttpClient.retry({
          while: isRetryable,
          schedule: Schedule.exponential(50),
          times: 3
        })
      )

      const latest = Effect.fn("RatesApi.latest")(function*(base: string) {
        const url = `${baseUrl.replace(/\/+$/, "")}/rates/${encodeURIComponent(base)}`
        return yield* client.get(url).pipe(
          Effect.flatMap(HttpClientResponse.schemaBodyJson(RatesResponse)),
          Effect.mapError((cause) =>
            isInvalidBody(cause)
              ? new InvalidResponseError({})
              : new RatesRequestError({ cause })
          )
        )
      })

      return RatesApi.of({ latest })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

const isRetryable = (error: HttpClientError.HttpClientError): boolean => {
  const reason = error.reason
  if (reason._tag === "TransportError") return true
  if (reason._tag === "StatusCodeError") return reason.response.status >= 500
  return false
}

// Body could not be read or did not match the schema.
const isInvalidBody = (cause: unknown): boolean =>
  Schema.isSchemaError(cause) ||
  (HttpClientError.isHttpClientError(cause) &&
    (cause.reason._tag === "DecodeError" || cause.reason._tag === "EmptyBodyError"))

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const program = Effect.gen(function*() {
  const [base, quote] = process.argv.slice(2)
  if (!base || !quote) {
    return yield* new UsageError({ message: "usage: npx tsx src/main.ts <BASE> <QUOTE>" })
  }

  const api = yield* RatesApi
  const body = yield* api.latest(base)

  if (!Object.hasOwn(body.rates, quote)) {
    return yield* new UnknownCurrencyError({ currency: quote })
  }

  const rate = body.rates[quote]
  yield* Console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
  return 0
})

const describeFailure = (e: UsageError | RatesRequestError): string =>
  e._tag === "UsageError" ? e.message : `request failed: ${String(e.cause)}`

const main = program.pipe(
  Effect.provide(RatesApi.layer),
  Effect.catchTag("UnknownCurrencyError", (e) =>
    Console.error(`unknown currency: ${e.currency}`).pipe(Effect.as(1))),
  Effect.catchTag("InvalidResponseError", () =>
    Console.error("invalid response").pipe(Effect.as(2))),
  Effect.catch((e) => Console.error(describeFailure(e)).pipe(Effect.as(3)))
)

process.exitCode = await Effect.runPromise(main)
