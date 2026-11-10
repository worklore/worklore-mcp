import { Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientRequest, HttpClientResponse } from "effect/http"

const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})

class InvalidResponse extends Error {}
class UnknownCurrency extends Error {
  constructor(readonly currency: string) {
    super(`unknown currency: ${currency}`)
  }
}

class Rates extends Context.Service<Rates, {
  readonly get: (base: string) => Effect.Effect<typeof RatesResponse.Type, InvalidResponse | Error>
}>()("Rates") {
  static readonly layer = Layer.effect(
    Rates,
    Effect.gen(function* () {
      const baseUrl = process.env.RATES_URL
      if (!baseUrl) return yield* Effect.fail(new Error("RATES_URL is required"))

      const client = (yield* HttpClient.HttpClient).pipe(
        HttpClient.mapRequest(HttpClientRequest.prependUrl(baseUrl.replace(/\/$/, ""))),
        HttpClient.filterStatusOk,
        HttpClient.retryTransient({ schedule: Schedule.exponential(50), times: 3 })
      )

      return Rates.of({
        get: (base) => client.get(`/rates/${encodeURIComponent(base)}`).pipe(
          Effect.flatMap((response) => HttpClientResponse.schemaBodyJson(RatesResponse)(response).pipe(
            Effect.mapError(() => new InvalidResponse())
          ))
        )
      })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

const [base, quote] = process.argv.slice(2)

const program = Effect.gen(function* () {
  if (!base || !quote) return yield* Effect.fail(new Error("Usage: main.ts BASE QUOTE"))
  const rates = yield* Rates
  const response = yield* rates.get(base)
  const rate = Object.hasOwn(response.rates, quote) ? response.rates[quote] : undefined
  if (rate === undefined) return yield* Effect.fail(new UnknownCurrency(quote))
  return `1 ${base} = ${rate.toFixed(4)} ${quote}`
}).pipe(Effect.provide(Rates.layer))

Effect.runPromise(program).then(
  (output) => { console.log(output) },
  (error: unknown) => {
    if (error instanceof UnknownCurrency) {
      console.error(error.message)
      process.exitCode = 1
    } else if (error instanceof InvalidResponse) {
      console.error("invalid response")
      process.exitCode = 2
    } else {
      console.error(error)
      process.exitCode = 3
    }
  }
)
