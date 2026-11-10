import { Context, Effect, Layer, Schedule, Schema } from "effect"
import * as HttpClient from "effect/http/HttpClient"
import { NodeHttpClient } from "@effect/platform-node"

const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number),
})

class InvalidResponse extends Error {}
class UnknownCurrency extends Error {}
class TransientFailure extends Error {}
class RequestFailure extends Error {}

type Rates = typeof RatesResponse.Type
class RatesApi extends Context.Service<RatesApi, {
  get: (base: string) => Effect.Effect<Rates, InvalidResponse | TransientFailure | RequestFailure>
}>()("RatesApi") {}

const RatesApiLive = Layer.effect(RatesApi, Effect.gen(function* () {
  const client = yield* HttpClient.HttpClient
  const baseUrl = process.env.RATES_URL
  return {
    get: (base: string) => Effect.gen(function* () {
      if (!baseUrl) return yield* Effect.fail(new RequestFailure("RATES_URL is missing"))
      let url: URL
      try {
        url = new URL(`${baseUrl.replace(/\/$/, "")}/rates/${encodeURIComponent(base)}`)
      } catch {
        return yield* Effect.fail(new RequestFailure("invalid RATES_URL"))
      }
      const response = yield* HttpClient.get(url).pipe(
        Effect.provideService(HttpClient.HttpClient, client),
        Effect.mapError(() => new TransientFailure()),
      )
      if (response.status >= 500) return yield* Effect.fail(new TransientFailure())
      if (response.status < 200 || response.status >= 300) return yield* Effect.fail(new RequestFailure())
      const body = yield* response.json.pipe(Effect.mapError(() => new InvalidResponse()))
      return yield* Schema.decodeUnknownEffect(RatesResponse)(body).pipe(
        Effect.mapError(() => new InvalidResponse()),
      )
    }).pipe(Effect.retry({ schedule: Schedule.exponential("50 millis"), times: 3, while: (error) => error instanceof TransientFailure })),
  }
})).pipe(Layer.provide(NodeHttpClient.layerUndici))

const [base, quote] = process.argv.slice(2)
const program = Effect.gen(function* () {
  if (!base || !quote) return yield* Effect.fail(new RequestFailure("usage: npx tsx src/main.ts BASE QUOTE"))
  const api = yield* RatesApi
  const response = yield* api.get(base)
  const rate = response.rates[quote]
  if (rate === undefined) return yield* Effect.fail(new UnknownCurrency(quote))
  console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
}).pipe(Effect.provide(RatesApiLive))

Effect.runPromise(program.pipe(Effect.match({ onSuccess: () => {}, onFailure: (error) => {
  if (error instanceof UnknownCurrency) {
    console.error(`unknown currency: ${error.message}`)
    process.exitCode = 1
  } else if (error instanceof InvalidResponse) {
    console.error("invalid response")
    process.exitCode = 2
  } else {
    console.error(error instanceof Error ? error.message : String(error))
    process.exitCode = 3
  }
}}))).catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : String(error))
  process.exitCode = 3
})
