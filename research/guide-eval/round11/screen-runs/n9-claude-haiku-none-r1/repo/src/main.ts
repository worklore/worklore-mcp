import { Cause, Config, Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientError } from "effect/http"

// Response body of GET {RATES_URL}/rates/{BASE}
export const RatesBody = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
export type RatesBody = typeof RatesBody.Type

// Network failure or non-2xx response that was not recovered by retrying.
export class RatesRequestError extends Schema.TaggedError<RatesRequestError>()("RatesRequestError", {
  cause: Schema.Defect()
}) {}

// Body was not JSON or did not match RatesBody.
export class InvalidResponseError extends Schema.TaggedError<InvalidResponseError>()("InvalidResponseError", {
  cause: Schema.Defect()
}) {}

// The quote currency is missing from the rates table.
export class UnknownCurrencyError extends Schema.TaggedError<UnknownCurrencyError>()("UnknownCurrencyError", {
  code: Schema.String
}) {}

export class RatesApi extends Context.Service<RatesApi, {
  readonly latest: (base: string) => Effect.Effect<RatesBody, RatesRequestError | InvalidResponseError>
}>()("fx-cli/RatesApi") {
  static readonly layer = Layer.effect(
    RatesApi,
    Effect.gen(function*() {
      const baseUrl = yield* Config.NonEmptyString("RATES_URL")
      // Non-2xx responses become StatusCodeError so the retry predicate can see them.
      const http = (yield* HttpClient.HttpClient).pipe(HttpClient.filterStatusOk)

      // Retry network errors and 5xx responses only.
      const isTransient = (error: HttpClientError.HttpClientError): boolean => {
        const reason = error.reason
        return reason._tag === "TransportError" ||
          (reason._tag === "StatusCodeError" && reason.response.status >= 500)
      }

      const latest = Effect.fn("RatesApi.latest")(function*(base: string) {
        const url = `${baseUrl}/rates/${encodeURIComponent(base)}`

        const response = yield* http.get(url).pipe(
          Effect.retry({ schedule: Schedule.exponential(50), times: 3, while: isTransient }),
          Effect.mapError((cause) => new RatesRequestError({ cause }))
        )

        return yield* response.json.pipe(
          Effect.mapError((cause) => {
            const emptyOrUnparsable = cause.reason._tag === "DecodeError" || cause.reason._tag === "EmptyBodyError"
            return emptyOrUnparsable
              ? new InvalidResponseError({ cause })
              : new RatesRequestError({ cause })
          }),
          Effect.flatMap((json) =>
            Schema.decodeUnknownEffect(RatesBody)(json).pipe(
              Effect.mapError((cause) => new InvalidResponseError({ cause }))
            )
          )
        )
      })

      return RatesApi.of({ latest })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

const describe = (cause: unknown): string => (cause instanceof Error ? cause.message : String(cause))

const report = (message: string, code: number) =>
  Effect.sync(() => {
    console.error(message)
    return code
  })

const program = (base: string, quote: string) =>
  Effect.gen(function*() {
    const api = yield* RatesApi
    const body = yield* api.latest(base)
    if (!Object.hasOwn(body.rates, quote)) {
      return yield* new UnknownCurrencyError({ code: quote })
    }
    const rate = body.rates[quote]
    console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
    return 0
  })

const [base, quote] = process.argv.slice(2)

const main = base === undefined || quote === undefined || base === "" || quote === ""
  ? report("usage: npx tsx src/main.ts BASE QUOTE", 3)
  : program(base, quote).pipe(
    Effect.provide(RatesApi.layer),
    Effect.catchTags({
      UnknownCurrencyError: (error) => report(`unknown currency: ${error.code}`, 1),
      InvalidResponseError: () => report("invalid response", 2),
      RatesRequestError: (error) => report(`error: ${describe(error.cause)}`, 3),
      ConfigError: () => report("error: RATES_URL is not set or is empty", 3)
    }),
    // Defects and anything else.
    Effect.catchCause((cause) => report(`error: ${Cause.pretty(cause)}`, 3))
  )

process.exitCode = await Effect.runPromise(main)
