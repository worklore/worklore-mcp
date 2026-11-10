import { Cause, Config, Context, Effect, Exit, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientError, HttpClientRequest, HttpClientResponse } from "effect/http"

export class InvalidResponseError extends Schema.TaggedError<InvalidResponseError>()(
  "InvalidResponseError",
  {}
) {}

export class UnknownCurrencyError extends Schema.TaggedError<UnknownCurrencyError>()(
  "UnknownCurrencyError",
  { currency: Schema.String }
) {}

export const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
export type RatesResponse = typeof RatesResponse.Type

export class RatesService extends Context.Service<RatesService, {
  readonly getRates: (base: string) => Effect.Effect<RatesResponse, InvalidResponseError | unknown>
}>()("app/RatesService") {
  static readonly layer = Layer.effect(
    RatesService,
    Effect.gen(function*() {
      const baseUrl = yield* Config.String("RATES_URL").pipe(
        Config.map((url) => url.replace(/\/+$/, ""))
      )

      const client = (yield* HttpClient.HttpClient).pipe(
        HttpClient.mapRequest((req) =>
          req.pipe(
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

      const getRates = (base: string) =>
        client.get(`/rates/${base}`).pipe(
          Effect.flatMap(HttpClientResponse.schemaBodyJson(RatesResponse)),
          Effect.catchIf(
            (err) =>
              Schema.isSchemaError(err) ||
              (HttpClientError.isHttpClientError(err) && err.reason._tag === "DecodeError"),
            () => new InvalidResponseError()
          )
        )

      return RatesService.of({ getRates })
    })
  ).pipe(
    Layer.provide(FetchHttpClient.layer)
  )
}

const main = Effect.gen(function*() {
  const [base, quote] = process.argv.slice(2)
  if (!base || !quote) {
    return yield* Effect.fail(new Error("Usage: npx tsx src/main.ts <BASE> <QUOTE>"))
  }

  const ratesService = yield* RatesService
  const response = yield* ratesService.getRates(base)

  const rate = response.rates[quote]
  if (rate === undefined) {
    return yield* Effect.fail(new UnknownCurrencyError({ currency: quote }))
  }

  return { base, quote, rate }
})

const exit = await Effect.runPromiseExit(
  main.pipe(Effect.provide(RatesService.layer))
)

Exit.match(exit, {
  onSuccess: ({ base, quote, rate }) => {
    console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
    process.exit(0)
  },
  onFailure: (cause) => {
    const error = Cause.squash(cause)

    if (error instanceof UnknownCurrencyError) {
      console.error(`unknown currency: ${error.currency}`)
      process.exit(1)
    }

    if (error instanceof InvalidResponseError) {
      console.error("invalid response")
      process.exit(2)
    }

    process.exit(3)
  }
})
