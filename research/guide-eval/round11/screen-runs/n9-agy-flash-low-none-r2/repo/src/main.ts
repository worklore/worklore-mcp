import { Cause, Console, Context, Effect, Exit, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientError, HttpClientResponse } from "effect/http"

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
  {}
) {}

export class RatesService extends Context.Service<RatesService, {
  readonly getRate: (
    base: string,
    quote: string
  ) => Effect.Effect<number, UnknownCurrencyError | InvalidResponseError | unknown>
}>()("app/RatesService") {
  static readonly layer = Layer.effect(
    RatesService,
    Effect.gen(function*() {
      const defaultClient = yield* HttpClient.HttpClient
      const rawBaseUrl = process.env.RATES_URL
      if (!rawBaseUrl) {
        return yield* Effect.fail(new Error("RATES_URL environment variable is not set"))
      }
      const baseUrl = rawBaseUrl.replace(/\/+$/, "")

      const client = defaultClient.pipe(
        HttpClient.filterStatusOk,
        HttpClient.retryTransient({
          schedule: Schedule.exponential(50),
          times: 3
        })
      )

      const getRate = (base: string, quote: string) =>
        Effect.gen(function*() {
          const response = yield* client.get(`${baseUrl}/rates/${encodeURIComponent(base)}`)
          const data = yield* HttpClientResponse.schemaBodyJson(RatesResponse)(response).pipe(
            Effect.mapError((err) => {
              if (
                Schema.isSchemaError(err) ||
                (HttpClientError.isHttpClientError(err) && err.reason._tag === "DecodeError")
              ) {
                return new InvalidResponseError()
              }
              return err
            })
          )

          const rate = data.rates[quote]
          if (typeof rate !== "number") {
            return yield* new UnknownCurrencyError({ currency: quote })
          }

          return rate
        })

      return RatesService.of({ getRate })
    })
  ).pipe(
    Layer.provide(FetchHttpClient.layer)
  )
}

const [base, quote] = process.argv.slice(2)

const program = Effect.gen(function*() {
  if (!base || !quote) {
    return yield* Effect.fail(new Error("Usage: npx tsx src/main.ts <base> <quote>"))
  }

  const ratesService = yield* RatesService
  const rate = yield* ratesService.getRate(base, quote)
  yield* Console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
}).pipe(
  Effect.provide(RatesService.layer)
)

const exit = await Effect.runPromiseExit(program)

Exit.match(exit, {
  onSuccess: () => {
    process.exit(0)
  },
  onFailure: (cause) => {
    const error = Cause.squash(cause)

    if (error instanceof UnknownCurrencyError || (error as any)?._tag === "UnknownCurrencyError") {
      process.stderr.write(`unknown currency: ${(error as UnknownCurrencyError).currency}\n`)
      process.exit(1)
    }

    if (error instanceof InvalidResponseError || (error as any)?._tag === "InvalidResponseError") {
      process.stderr.write("invalid response\n")
      process.exit(2)
    }

    process.exit(3)
  }
})
