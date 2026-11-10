import { NodeRuntime } from "@effect/platform-node"
import { Config, Console, Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientError, HttpClientRequest, HttpClientResponse } from "effect/http"

// ---------------------------------------------------------------------------
// Domain
// ---------------------------------------------------------------------------

const RatesBody = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
type RatesBody = Schema.Schema.Type<typeof RatesBody>

/** The rates service could not be reached or answered with a non-retried failure. */
export class RatesUnavailable extends Schema.TaggedError<RatesUnavailable>()("RatesUnavailable", {
  cause: Schema.Defect()
}) {}

/** The response body did not match the expected shape. */
export class InvalidResponse extends Schema.TaggedError<InvalidResponse>()("InvalidResponse", {}) {}

/** The requested quote currency is not present in the rates. */
export class UnknownCurrency extends Schema.TaggedError<UnknownCurrency>()("UnknownCurrency", {
  code: Schema.String
}) {}

/** Missing or malformed command-line arguments. */
export class Usage extends Schema.TaggedError<Usage>()("Usage", {}) {}

// ---------------------------------------------------------------------------
// Rates API service
// ---------------------------------------------------------------------------

const isTransient = (error: HttpClientError.HttpClientError): boolean => {
  const reason = error.reason
  if (reason._tag === "TransportError") return true
  if (reason._tag === "StatusCodeError") return reason.response.status >= 500
  return false
}

export class RatesApi extends Context.Service<RatesApi, {
  readonly latest: (base: string) => Effect.Effect<RatesBody, RatesUnavailable | InvalidResponse>
}>()("fx/RatesApi") {
  static readonly layer = Layer.effect(
    RatesApi,
    Effect.gen(function*() {
      const baseUrl = yield* Config.String("RATES_URL")
      const http = (yield* HttpClient.HttpClient).pipe(
        HttpClient.filterStatusOk,
        HttpClient.retry({
          schedule: Schedule.exponential(50),
          times: 3,
          while: isTransient
        })
      )

      const latest = Effect.fn("RatesApi.latest")(function*(base: string) {
        const url = `${baseUrl}/rates/${encodeURIComponent(base)}`
        const response = yield* http.execute(
          HttpClientRequest.get(url).pipe(HttpClientRequest.acceptJson)
        ).pipe(Effect.mapError((cause) => new RatesUnavailable({ cause })))

        return yield* HttpClientResponse.schemaBodyJson(RatesBody)(response).pipe(
          Effect.mapError((cause) => {
            // Undecodable JSON or a body that fails the schema is an invalid response;
            // anything else raised while reading the body is a transport failure.
            const invalid = Schema.isSchemaError(cause) ||
              (HttpClientError.isHttpClientError(cause) && cause.reason._tag === "DecodeError")
            return invalid ? new InvalidResponse() : new RatesUnavailable({ cause })
          })
        )
      })

      return RatesApi.of({ latest })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const exitCodeFor = (error: unknown): { readonly code: number; readonly message: string } => {
  if (error instanceof UnknownCurrency) return { code: 1, message: `unknown currency: ${error.code}` }
  if (error instanceof InvalidResponse) return { code: 2, message: "invalid response" }
  if (error instanceof Usage) {
    return { code: 3, message: "usage: npx tsx src/main.ts <BASE> <QUOTE>" }
  }
  if (error instanceof RatesUnavailable) {
    const cause = error.cause instanceof Error ? error.cause.message : String(error.cause)
    return { code: 3, message: `error: rates service unavailable (${cause})` }
  }
  return { code: 3, message: `error: ${error instanceof Error ? error.message : String(error)}` }
}

const program = Effect.gen(function*() {
  const [base, quote] = process.argv.slice(2)
  if (base === undefined || quote === undefined) {
    return yield* new Usage()
  }

  const api = yield* RatesApi
  const body = yield* api.latest(base)
  if (!Object.hasOwn(body.rates, quote)) {
    return yield* new UnknownCurrency({ code: quote })
  }

  const rate = body.rates[quote]!
  yield* Console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
}).pipe(
  Effect.provide(RatesApi.layer),
  Effect.catch((error) => {
    const { code, message } = exitCodeFor(error)
    return Console.error(message).pipe(
      Effect.andThen(Effect.sync(() => {
        process.exitCode = code
      }))
    )
  })
)

NodeRuntime.runMain(program)
