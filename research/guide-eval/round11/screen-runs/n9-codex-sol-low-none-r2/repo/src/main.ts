import { Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient } from "effect/http"

const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number),
})

class InvalidResponse extends Error { readonly _tag = "InvalidResponse" }
class UnknownCurrency extends Error { readonly _tag = "UnknownCurrency" }
class TransientFailure extends Error { readonly _tag = "TransientFailure" }
class RequestFailure extends Error { readonly _tag = "RequestFailure" }

type Rates = typeof RatesResponse.Type
interface RatesApi {
  readonly getRates: (base: string) => Effect.Effect<Rates, InvalidResponse | TransientFailure | RequestFailure>
}
const RatesApi = Context.Service<RatesApi>("RatesApi")

const RatesApiLive = Layer.effect(RatesApi, Effect.gen(function* () {
  const client = yield* HttpClient.HttpClient
  return {
    getRates: (base: string) => Effect.gen(function* () {
      const baseUrl = process.env.RATES_URL
      if (!baseUrl) return yield* Effect.fail(new RequestFailure("RATES_URL is missing"))
      const url = `${baseUrl.replace(/\/$/, "")}/rates/${encodeURIComponent(base)}`
      const response = yield* client.get(url).pipe(
        Effect.mapError((error) => error.reason._tag === "TransportError"
          ? new TransientFailure()
          : new RequestFailure()),
      )
      if (response.status >= 500) return yield* Effect.fail(new TransientFailure())
      if (response.status < 200 || response.status >= 300) return yield* Effect.fail(new RequestFailure())
      const body = yield* response.json.pipe(Effect.mapError(() => new InvalidResponse()))
      return yield* Schema.decodeUnknownEffect(RatesResponse)(body).pipe(
        Effect.mapError(() => new InvalidResponse()),
      )
    }).pipe(Effect.retry({ times: 3, schedule: Schedule.exponential("50 millis"), while: (error) => error._tag === "TransientFailure" })),
  }
})).pipe(Layer.provide(FetchHttpClient.layer))

const [base, quote] = process.argv.slice(2)
const program = Effect.gen(function* () {
  if (!base || !quote) return yield* Effect.fail(new RequestFailure("missing currency"))
  const api = yield* RatesApi
  const data = yield* api.getRates(base)
  const rate = data.rates[quote]
  if (rate === undefined) return yield* Effect.fail(new UnknownCurrency())
  console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
}).pipe(Effect.provide(RatesApiLive))

Effect.runPromise(program).catch((error: unknown) => {
  if (error instanceof UnknownCurrency) {
    console.error(`unknown currency: ${quote}`)
    process.exitCode = 1
  } else if (error instanceof InvalidResponse) {
    console.error("invalid response")
    process.exitCode = 2
  } else {
    console.error("request failed")
    process.exitCode = 3
  }
})
