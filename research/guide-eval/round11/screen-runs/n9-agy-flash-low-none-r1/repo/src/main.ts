import { Config, Console, Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientError, HttpClientResponse } from "effect/http"

export const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
export type RatesResponse = typeof RatesResponse.Type

export class UnknownCurrencyError extends Schema.TaggedError<UnknownCurrencyError>()("UnknownCurrencyError", {
  currency: Schema.String
}) {}

export class InvalidResponseError extends Schema.TaggedError<InvalidResponseError>()("InvalidResponseError", {
  cause: Schema.Defect()
}) {}

export class RatesApi extends Context.Service<RatesApi, {
  readonly getRates: (base: string) => Effect.Effect<RatesResponse, InvalidResponseError | unknown>
}>()("fx/RatesApi") {
  static readonly layer = Layer.effect(
    RatesApi,
    Effect.gen(function*() {
      const ratesUrl = (yield* Config.String("RATES_URL")).replace(/\/+$/, "")
      const baseClient = yield* HttpClient.HttpClient
      const client = baseClient.pipe(
        HttpClient.filterStatusOk,
        HttpClient.retryTransient({
          schedule: Schedule.exponential("50 millis"),
          times: 3
        })
      )

      const getRates = (base: string) =>
        client.get(`${ratesUrl}/rates/${base}`).pipe(
          Effect.flatMap(HttpClientResponse.schemaBodyJson(RatesResponse)),
          Effect.mapError((err) => {
            if (
              Schema.isSchemaError(err) ||
              (HttpClientError.isHttpClientError(err) && err.reason._tag === "DecodeError")
            ) {
              return new InvalidResponseError({ cause: err })
            }
            return err
          })
        )

      return RatesApi.of({ getRates })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

export const getRate = (base: string, quote: string) =>
  Effect.gen(function*() {
    const api = yield* RatesApi
    const data = yield* api.getRates(base)
    const rate = data.rates[quote]
    if (rate === undefined) {
      return yield* new UnknownCurrencyError({ currency: quote })
    }
    return rate
  })

const [base, quote] = process.argv.slice(2)

const program = Effect.gen(function*() {
  if (!base || !quote) {
    yield* Console.error("Usage: npx tsx src/main.ts <BASE> <QUOTE>")
    return 3
  }

  const rate = yield* getRate(base, quote)
  yield* Console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
  return 0
}).pipe(
  Effect.provide(RatesApi.layer),
  Effect.catch((err: unknown) => {
    if (err instanceof UnknownCurrencyError) {
      return Console.error(`unknown currency: ${err.currency}`).pipe(Effect.as(1))
    }
    if (
      err instanceof InvalidResponseError ||
      Schema.isSchemaError(err) ||
      (HttpClientError.isHttpClientError(err) && err.reason._tag === "DecodeError")
    ) {
      return Console.error("invalid response").pipe(Effect.as(2))
    }
    return Console.error(err).pipe(Effect.as(3))
  })
)

const exitCode = await Effect.runPromise(program)
process.exit(exitCode)
