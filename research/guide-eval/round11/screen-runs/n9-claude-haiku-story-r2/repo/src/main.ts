import { Config, Context, Effect, flow, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientError, HttpClientRequest, HttpClientResponse } from "effect/http"

const RatesBody = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
type RatesBody = typeof RatesBody.Type

export class UnknownCurrency extends Schema.TaggedError<UnknownCurrency>()("UnknownCurrency", {
  code: Schema.String
}) {}

export class InvalidResponse extends Schema.TaggedError<InvalidResponse>()("InvalidResponse", {}) {}

export class Usage extends Schema.TaggedError<Usage>()("Usage", {}) {}

// Transport failures while reading the body are "other" failures; anything
// that fails to decode or parse is an invalid response.
const toBodyError = (cause: HttpClientError.HttpClientError | Schema.SchemaError): HttpClientError.HttpClientError | InvalidResponse =>
  HttpClientError.isHttpClientError(cause) && cause.reason._tag === "TransportError"
    ? cause
    : new InvalidResponse()

export class Rates extends Context.Service<Rates, {
  readonly latest: (
    base: string
  ) => Effect.Effect<RatesBody, HttpClientError.HttpClientError | InvalidResponse | Config.ConfigError>
}>()("fx-cli/Rates") {
  static readonly layer = Layer.effect(
    Rates,
    Effect.gen(function*() {
      const baseUrl = (yield* Config.String("RATES_URL")).replace(/\/+$/, "")

      const client = (yield* HttpClient.HttpClient).pipe(
        HttpClient.mapRequest(HttpClientRequest.acceptJson),
        // Non-2xx responses become HttpClientError values so retries can see them.
        HttpClient.filterStatusOk,
        // Retries network errors and transient statuses (5xx, 408, 429) up to
        // 3 times after the first attempt, with 50 ms, 100 ms, 200 ms backoff.
        HttpClient.retryTransient({
          schedule: Schedule.exponential(50),
          times: 3
        })
      )

      return Rates.of({
        latest: Effect.fn("Rates.latest")(function*(base: string) {
          const response = yield* client.get(`${baseUrl}/rates/${encodeURIComponent(base)}`)
          return yield* HttpClientResponse.schemaBodyJson(RatesBody)(response).pipe(
            Effect.mapError(toBodyError)
          )
        })
      })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

type Outcome = { readonly code: number; readonly stdout: string; readonly stderr: string }

const program = Effect.gen(function*() {
  const [base, quote] = process.argv.slice(2)
  if (base === undefined || quote === undefined) {
    return yield* new Usage()
  }
  const rates = yield* Rates
  const body = yield* rates.latest(base)
  if (!Object.prototype.hasOwnProperty.call(body.rates, quote)) {
    return yield* new UnknownCurrency({ code: quote })
  }
  return `1 ${base} = ${body.rates[quote].toFixed(4)} ${quote}`
}).pipe(Effect.provide(Rates.layer))

const outcome: Outcome = await Effect.runPromise(
  program.pipe(
    Effect.map((line): Outcome => ({ code: 0, stdout: `${line}\n`, stderr: "" })),
    Effect.catchTag("UnknownCurrency", (e) =>
      Effect.succeed<Outcome>({ code: 1, stdout: "", stderr: `unknown currency: ${e.code}\n` })),
    Effect.catchTag("InvalidResponse", () =>
      Effect.succeed<Outcome>({ code: 2, stdout: "", stderr: "invalid response\n" })),
    Effect.catchTag("Usage", () =>
      Effect.succeed<Outcome>({ code: 3, stdout: "", stderr: "usage: npx tsx src/main.ts BASE QUOTE\n" })),
    Effect.catch((e) =>
      Effect.succeed<Outcome>({ code: 3, stdout: "", stderr: `request failed: ${describe(e)}\n` }))
  )
).catch((defect): Outcome => ({ code: 3, stdout: "", stderr: `unexpected error: ${describe(defect)}\n` }))

process.stdout.write(outcome.stdout)
process.stderr.write(outcome.stderr)
process.exitCode = outcome.code

function describe(e: unknown): string {
  if (e instanceof Error) return e.message
  if (typeof e === "object" && e !== null && "_tag" in e) return String(e._tag)
  return String(e)
}
