import { Config, Console, Context, Effect, flow, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientRequest, HttpClientResponse } from "effect/http"

export const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
export type RatesResponse = typeof RatesResponse.Type

export class UnknownCurrencyError extends Schema.TaggedError<UnknownCurrencyError>()(
  "UnknownCurrencyError",
  {
    currency: Schema.String
  }
) {}

export class InvalidResponseError extends Schema.TaggedError<InvalidResponseError>()(
  "InvalidResponseError",
  {
    cause: Schema.Unknown
  }
) {}

export class RatesError extends Schema.TaggedError<RatesError>()(
  "RatesError",
  {
    cause: Schema.Unknown
  }
) {}

export class RatesService extends Context.Service<RatesService, {
  readonly getRate: (
    base: string,
    quote: string
  ) => Effect.Effect<number, UnknownCurrencyError | InvalidResponseError | RatesError>
}>()("app/RatesService") {
  static readonly layer = Layer.effect(
    RatesService,
    Effect.gen(function*() {
      const baseUrl = yield* Config.String("RATES_URL")

      const client = (yield* HttpClient.HttpClient).pipe(
        HttpClient.mapRequest(
          flow(
            HttpClientRequest.prependUrl(baseUrl),
            HttpClientRequest.acceptJson
          )
        ),
        HttpClient.filterStatusOk,
        HttpClient.retryTransient({
          schedule: Schedule.exponential(50),
          times: 3
        })
      )

      const getRate = (base: string, quote: string) =>
        client.get(`/rates/${encodeURIComponent(base)}`).pipe(
          Effect.flatMap(HttpClientResponse.schemaBodyJson(RatesResponse)),
          Effect.mapError((err) => {
            if (err._tag === "SchemaError") {
              return new InvalidResponseError({ cause: err })
            }
            if (err.reason._tag === "DecodeError") {
              return new InvalidResponseError({ cause: err })
            }
            return new RatesError({ cause: err })
          }),
          Effect.flatMap((data) => {
            const rate = data.rates[quote]
            if (typeof rate !== "number") {
              return Effect.fail(new UnknownCurrencyError({ currency: quote }))
            }
            return Effect.succeed(rate)
          })
        )

      return RatesService.of({ getRate })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

const main = Effect.gen(function*() {
  const args = process.argv.slice(2)
  const base = args[0]
  const quote = args[1]

  if (!base || !quote) {
    return yield* Effect.fail(new RatesError({ cause: "Usage: npx tsx src/main.ts <base> <quote>" }))
  }

  const ratesService = yield* RatesService
  const rate = yield* ratesService.getRate(base, quote)
  yield* Console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
})

const runnable = main.pipe(
  Effect.provide(RatesService.layer),
  Effect.catchTags({
    UnknownCurrencyError: (err) =>
      Console.error(`unknown currency: ${err.currency}`).pipe(
        Effect.andThen(
          Effect.sync(() => {
            process.exitCode = 1
          })
        )
      ),
    InvalidResponseError: () =>
      Console.error("invalid response").pipe(
        Effect.andThen(
          Effect.sync(() => {
            process.exitCode = 2
          })
        )
      )
  }),
  Effect.catch(() =>
    Effect.sync(() => {
      process.exitCode = 3
    })
  ),
  Effect.catchDefect(() =>
    Effect.sync(() => {
      process.exitCode = 3
    })
  )
)

await Effect.runPromise(runnable)
