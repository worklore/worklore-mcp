import { Config, Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientRequest, HttpClientResponse } from "effect/http"

class Rates extends Schema.Class<Rates>("Rates")({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
}) {}

class InvalidResponse extends Schema.TaggedError<InvalidResponse>()("InvalidResponse", {}) {}
class RatesUnavailable extends Schema.TaggedError<RatesUnavailable>()("RatesUnavailable", {
  cause: Schema.Defect()
}) {}
class UnknownCurrency extends Schema.TaggedError<UnknownCurrency>()("UnknownCurrency", {
  code: Schema.String
}) {}

class RatesApi extends Context.Service<RatesApi, {
  latest(base: string): Effect.Effect<Rates, InvalidResponse | RatesUnavailable>
}>()("fx-cli/RatesApi") {
  static readonly layer = Layer.effect(
    RatesApi,
    Effect.gen(function*() {
      const baseUrl = yield* Config.String("RATES_URL")
      const client = (yield* HttpClient.HttpClient).pipe(
        HttpClient.mapRequest(HttpClientRequest.prependUrl(baseUrl)),
        HttpClient.filterStatusOk,
        HttpClient.retryTransient({ schedule: Schedule.exponential(50), times: 3 })
      )
      const latest = Effect.fn("RatesApi.latest")(function*(base: string) {
        const response = yield* client.get(`/rates/${base}`).pipe(
          Effect.mapError((cause) => new RatesUnavailable({ cause }))
        )
        return yield* HttpClientResponse.schemaBodyJson(Rates)(response).pipe(
          Effect.mapError(() => new InvalidResponse())
        )
      })
      return RatesApi.of({ latest })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

const program = Effect.fn("main")(function*(base: string, quote: string) {
  const api = yield* RatesApi
  const rates = yield* api.latest(base)
  const rate = rates.rates[quote]
  if (rate === undefined) return yield* new UnknownCurrency({ code: quote })
  yield* Effect.sync(() => console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`))
})

const [base = "", quote = ""] = process.argv.slice(2)

const code = await program(base, quote).pipe(
  Effect.as(0),
  Effect.catchTags({
    UnknownCurrency: (e) => Effect.sync(() => { console.error(`unknown currency: ${e.code}`); return 1 }),
    InvalidResponse: () => Effect.sync(() => { console.error("invalid response"); return 2 })
  }),
  Effect.catch((e) => Effect.sync(() => { console.error(String(e)); return 3 })),
  Effect.provide(RatesApi.layer),
  Effect.catchCause(() => Effect.succeed(3)),
  Effect.runPromise
)
process.exitCode = code
