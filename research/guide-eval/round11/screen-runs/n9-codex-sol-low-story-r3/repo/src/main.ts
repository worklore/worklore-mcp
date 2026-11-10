import { Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientRequest } from "effect/http"

const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})

class InvalidResponse extends Schema.TaggedError<InvalidResponse>()("InvalidResponse", {}) {}
class UnknownCurrency extends Schema.TaggedError<UnknownCurrency>()("UnknownCurrency", {
  code: Schema.String
}) {}

class Rates extends Context.Service<Rates, {
  get(base: string): Effect.Effect<typeof RatesResponse.Type, InvalidResponse | Error>
}>()("fx-cli/Rates") {
  static readonly layer = Layer.effect(Rates, Effect.gen(function*() {
    const client = (yield* HttpClient.HttpClient).pipe(
      HttpClient.filterStatusOk,
      HttpClient.retryTransient({ schedule: Schedule.exponential(50), times: 3 })
    )

    return Rates.of({
      get: (base) => Effect.gen(function*() {
        const root = process.env.RATES_URL
        if (!root) return yield* Effect.fail(new Error("RATES_URL is required"))
        const url = `${root.replace(/\/$/, "")}/rates/${encodeURIComponent(base)}`
        const response = yield* client.execute(HttpClientRequest.get(url))
        const body = yield* response.json.pipe(Effect.mapError(() => new InvalidResponse()))
        return yield* Schema.decodeUnknownEffect(RatesResponse)(body).pipe(
          Effect.mapError(() => new InvalidResponse())
        )
      })
    })
  })).pipe(Layer.provide(FetchHttpClient.layer))
}

const [base, quote] = process.argv.slice(2)

const program = Effect.gen(function*() {
  if (!base || !quote) return yield* Effect.fail(new Error("Usage: USD EUR"))
  const rates = yield* Rates
  const response = yield* rates.get(base)
  const rate = response.rates[quote]
  if (rate === undefined) return yield* new UnknownCurrency({ code: quote })
  return `1 ${base} = ${rate.toFixed(4)} ${quote}`
}).pipe(
  Effect.provide(Rates.layer),
  Effect.match({
    onSuccess: (line) => ({ code: 0, line, stderr: false }),
    onFailure: (error) => error instanceof UnknownCurrency
      ? { code: 1, line: `unknown currency: ${error.code}`, stderr: true }
      : error instanceof InvalidResponse
        ? { code: 2, line: "invalid response", stderr: true }
        : { code: 3, line: "request failed", stderr: true }
  })
)

Effect.runPromise(program).then(({ code, line, stderr }) => {
  (stderr ? console.error : console.log)(line)
  process.exitCode = code
}).catch(() => {
  console.error("request failed")
  process.exitCode = 3
})
