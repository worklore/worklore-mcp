import { Config, Console, Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientRequest } from "effect/http"

// ---------------------------------------------------------------------------
// Response shape
// ---------------------------------------------------------------------------

const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})

const decodeRatesJson = Schema.decodeUnknownEffect(Schema.fromJsonString(RatesResponse))

// ---------------------------------------------------------------------------
// Errors. Each one maps to an exit code in `failure` below.
// ---------------------------------------------------------------------------

export class UsageError extends Schema.TaggedError<UsageError>()("UsageError", {}) {}

export class UnknownCurrency extends Schema.TaggedError<UnknownCurrency>()("UnknownCurrency", {
  code: Schema.String
}) {}

export class InvalidResponse extends Schema.TaggedError<InvalidResponse>()("InvalidResponse", {}) {}

export class RatesUnavailable extends Schema.TaggedError<RatesUnavailable>()("RatesUnavailable", {
  message: Schema.String
}) {}

// ---------------------------------------------------------------------------
// Rates service. The base URL comes from RATES_URL. Transient failures
// (network errors, 408/429/5xx) are retried up to 3 times with exponential
// backoff starting at 50 ms.
// ---------------------------------------------------------------------------

export class Rates extends Context.Service<Rates, {
  readonly rate: (
    base: string,
    quote: string
  ) => Effect.Effect<number, UnknownCurrency | InvalidResponse | RatesUnavailable>
}>()("fx-cli/Rates") {
  static readonly layer = Layer.effect(
    Rates,
    Effect.gen(function*() {
      const baseUrl = (yield* Config.String("RATES_URL")).replace(/\/+$/, "")

      const client = (yield* HttpClient.HttpClient).pipe(
        // Non-2xx responses become errors, so the retry below can see them.
        HttpClient.filterStatusOk,
        HttpClient.retryTransient({
          schedule: Schedule.exponential(50),
          times: 3
        })
      )

      const rate = Effect.fnUntraced(function*(base: string, quote: string) {
        const url = `${baseUrl}/rates/${encodeURIComponent(base)}`

        const response = yield* client.execute(
          HttpClientRequest.get(url).pipe(HttpClientRequest.acceptJson)
        ).pipe(
          Effect.mapError((error) => new RatesUnavailable({ message: error.message }))
        )

        const text = yield* response.text.pipe(
          Effect.mapError((error) => new RatesUnavailable({ message: error.message }))
        )

        const body = yield* decodeRatesJson(text).pipe(
          Effect.mapError(() => new InvalidResponse())
        )

        if (!Object.hasOwn(body.rates, quote)) {
          return yield* new UnknownCurrency({ code: quote })
        }
        return body.rates[quote]!
      })

      return Rates.of({ rate })
    })
  ).pipe(
    Layer.provide(FetchHttpClient.layer)
  )
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const failure = (error: unknown): { readonly code: number; readonly message: string } => {
  if (error instanceof UnknownCurrency) return { code: 1, message: `unknown currency: ${error.code}` }
  if (error instanceof InvalidResponse) return { code: 2, message: "invalid response" }
  if (error instanceof UsageError) {
    return { code: 3, message: "usage: npx tsx src/main.ts BASE QUOTE" }
  }
  if (error instanceof RatesUnavailable) {
    return { code: 3, message: `rates service unavailable: ${error.message}` }
  }
  const detail = error instanceof Error ? error.message : String(error)
  return { code: 3, message: `error: ${detail}` }
}

const [base, quote] = process.argv.slice(2)

const program = Effect.gen(function*() {
  if (base === undefined || quote === undefined) {
    return yield* new UsageError()
  }
  const rates = yield* Rates
  const value = yield* rates.rate(base, quote)
  yield* Console.log(`1 ${base} = ${value.toFixed(4)} ${quote}`)
})

const main = program.pipe(
  Effect.provide(Rates.layer),
  Effect.matchEffect({
    onSuccess: () => Effect.succeed(0),
    onFailure: (error) => {
      const { code, message } = failure(error)
      return Console.error(message).pipe(Effect.as(code))
    }
  })
)

// A defect (bug) escapes as a rejected promise; treat it like any other failure.
process.exitCode = await Effect.runPromise(main).catch((defect: unknown) => {
  console.error(`error: ${defect instanceof Error ? defect.message : String(defect)}`)
  return 3
})
