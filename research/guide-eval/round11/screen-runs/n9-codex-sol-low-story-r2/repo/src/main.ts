import { Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientRequest } from "effect/http"

const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
type RatesResponse = Schema.Schema.Type<typeof RatesResponse>

class InvalidResponse extends Schema.TaggedError<InvalidResponse>()("InvalidResponse", {}) {}
class UnknownCurrency extends Schema.TaggedError<UnknownCurrency>()("UnknownCurrency", {
  code: Schema.String
}) {}

class RatesApi extends Context.Service<RatesApi, {
  getRates(base: string): Effect.Effect<RatesResponse, unknown>
}>()("fx-cli/RatesApi") {
  static readonly layer = Layer.effect(
    RatesApi,
    Effect.gen(function*() {
      const baseUrl = process.env.RATES_URL
      if (!baseUrl) return yield* Effect.fail(new Error("RATES_URL is required"))

      const client = (yield* HttpClient.HttpClient).pipe(
        HttpClient.mapRequest(HttpClientRequest.prependUrl(baseUrl.replace(/\/$/, ""))),
        HttpClient.filterStatusOk,
        HttpClient.retryTransient({ schedule: Schedule.exponential(50), times: 3 })
      )

      return RatesApi.of({
        getRates: (base) => client.get(`/rates/${encodeURIComponent(base)}`).pipe(
          Effect.flatMap((response) => response.json.pipe(
            Effect.mapError(() => new InvalidResponse())
          )),
          Effect.flatMap((body) => Schema.decodeUnknownEffect(RatesResponse)(body).pipe(
            Effect.mapError(() => new InvalidResponse())
          ))
        )
      })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

const [base, quote] = process.argv.slice(2)
const program = Effect.gen(function*() {
  if (!base || !quote) return yield* Effect.fail(new Error("expected base and quote currencies"))
  const api = yield* RatesApi
  const response = yield* api.getRates(base)
  if (!Object.hasOwn(response.rates, quote)) {
    return yield* new UnknownCurrency({ code: quote })
  }
  console.log(`1 ${base} = ${response.rates[quote].toFixed(4)} ${quote}`)
}).pipe(Effect.provide(RatesApi.layer))

Effect.runPromise(Effect.result(program)).then((result) => {
  if (result._tag === "Success") return
  const error = result.failure
  if (error instanceof UnknownCurrency) {
    console.error(`unknown currency: ${error.code}`)
    process.exitCode = 1
  } else if (error instanceof InvalidResponse) {
    console.error("invalid response")
    process.exitCode = 2
  } else {
    console.error("request failed")
    process.exitCode = 3
  }
}).catch(() => {
  console.error("request failed")
  process.exitCode = 3
})
