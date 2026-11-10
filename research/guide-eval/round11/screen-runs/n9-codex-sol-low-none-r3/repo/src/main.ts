import { Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientError } from "effect/http"

const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})

type RatesResponse = typeof RatesResponse.Type

class InvalidResponse extends Error {}
class UnknownCurrency extends Error {
  constructor(currency: string) {
    super(`unknown currency: ${currency}`)
  }
}
class HttpStatusError extends Error {
  constructor(readonly status: number) {
    super(`HTTP ${status}`)
  }
}

const RatesApi = Context.Service<{
  getRates: (base: string) => Effect.Effect<RatesResponse, InvalidResponse | HttpStatusError | HttpClientError.HttpClientError>
}>("RatesApi")

const RatesApiLive = Layer.effect(RatesApi, Effect.gen(function* () {
  const client = yield* HttpClient.HttpClient
  const baseUrl = process.env.RATES_URL
  return {
    getRates: (base: string) => Effect.gen(function* () {
      if (!baseUrl) return yield* Effect.fail(new Error("RATES_URL is required"))
      const url = `${baseUrl.replace(/\/$/, "")}/rates/${encodeURIComponent(base)}`
      const response = yield* Effect.retry(
        Effect.gen(function* () {
          const result = yield* client.get(url)
          if (result.status >= 400) return yield* Effect.fail(new HttpStatusError(result.status))
          return result
        }),
        {
          while: (error) => error instanceof HttpStatusError
            ? error.status >= 500 && error.status < 600
            : error instanceof HttpClientError.HttpClientError && error.reason._tag === "TransportError",
          times: 3,
          schedule: Schedule.exponential("50 millis")
        }
      )
      const body = yield* response.json.pipe(Effect.mapError(() => new InvalidResponse()))
      return yield* Schema.decodeUnknownEffect(RatesResponse)(body).pipe(
        Effect.mapError(() => new InvalidResponse())
      )
    })
  }
})).pipe(Layer.provide(FetchHttpClient.layer))

const [base, quote] = process.argv.slice(2)
const program = Effect.gen(function* () {
  if (!base || !quote) return yield* Effect.fail(new Error("usage: npx tsx src/main.ts BASE QUOTE"))
  const api = yield* RatesApi
  const rates = yield* api.getRates(base)
  const rate = rates.rates[quote]
  if (rate === undefined) return yield* Effect.fail(new UnknownCurrency(quote))
  return `1 ${base} = ${rate.toFixed(4)} ${quote}`
}).pipe(Effect.provide(RatesApiLive))

try {
  const result = await Effect.runPromise(Effect.match(program, {
    onFailure: (error) => ({ error }),
    onSuccess: (value) => ({ value })
  }))
  if ("value" in result) {
    console.log(result.value)
    process.exitCode = 0
  } else {
    const error = result.error
    console.error(error instanceof InvalidResponse ? "invalid response" : error.message)
    process.exitCode = error instanceof InvalidResponse ? 2 : error instanceof UnknownCurrency ? 1 : 3
  }
} catch (error) {
  console.error(error)
  process.exitCode = 3
}
