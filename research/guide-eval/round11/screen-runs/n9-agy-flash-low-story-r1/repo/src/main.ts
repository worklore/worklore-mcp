import { Cause, Config, Console, Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientError, HttpClientResponse } from "effect/http"

export const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
export type RatesResponse = typeof RatesResponse.Type

export class RatesService extends Context.Service<RatesService, {
  readonly getRates: (base: string) => Effect.Effect<RatesResponse, HttpClientError.HttpClientError | Schema.SchemaError>
}>()("app/RatesService") {
  static readonly layer = Layer.effect(
    RatesService,
    Effect.gen(function*() {
      const baseUrl = yield* Config.String("RATES_URL")
      const baseClient = yield* HttpClient.HttpClient
      const client = baseClient.pipe(
        HttpClient.filterStatusOk,
        HttpClient.retryTransient({
          times: 3,
          schedule: Schedule.exponential(50)
        })
      )

      const getRates = (base: string) =>
        client.get(`${baseUrl}/rates/${encodeURIComponent(base)}`).pipe(
          Effect.flatMap(HttpClientResponse.schemaBodyJson(RatesResponse))
        )

      return RatesService.of({ getRates })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

export class UnknownCurrencyError extends Schema.TaggedError<UnknownCurrencyError>()(
  "UnknownCurrencyError",
  { currency: Schema.String }
) {}

export const getRate = (base: string, quote: string) =>
  Effect.gen(function*() {
    const service = yield* RatesService
    const data = yield* service.getRates(base)
    const rate = data.rates[quote]
    if (rate === undefined) {
      return yield* new UnknownCurrencyError({ currency: quote })
    }
    return rate
  })

const [baseArg, quoteArg] = process.argv.slice(2)

const program = Effect.gen(function*() {
  if (!baseArg || !quoteArg) {
    return yield* Effect.fail(new Error("Usage: npx tsx src/main.ts <base> <quote>"))
  }
  const rate = yield* getRate(baseArg, quoteArg)
  yield* Console.log(`1 ${baseArg} = ${rate.toFixed(4)} ${quoteArg}`)
}).pipe(
  Effect.provide(RatesService.layer),
  Effect.matchCauseEffect({
    onSuccess: () => Effect.sync(() => process.exit(0)),
    onFailure: (cause) =>
      Effect.gen(function*() {
        const error = Cause.findErrorOption(cause)
        if (error._tag === "Some") {
          const err = error.value
          if (err instanceof UnknownCurrencyError) {
            yield* Console.error(`unknown currency: ${err.currency}`)
            process.exit(1)
          }
          if (
            Schema.isSchemaError(err) ||
            (HttpClientError.isHttpClientError(err) && err.reason._tag === "DecodeError")
          ) {
            yield* Console.error("invalid response")
            process.exit(2)
          }
        }
        process.exit(3)
      })
  })
)

Effect.runPromise(program)
