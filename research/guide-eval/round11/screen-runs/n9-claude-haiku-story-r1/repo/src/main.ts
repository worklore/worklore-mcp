import { Config, Context, Effect, Layer, Schedule, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientError, HttpClientResponse } from "effect/http"

// Response body of GET {RATES_URL}/rates/{BASE}
const RatesBody = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number)
})
type RatesBody = typeof RatesBody.Type

// Errors. Each maps to one exit code in `main` below.
export class UsageError extends Schema.TaggedError<UsageError>()("UsageError", {
  message: Schema.String
}) {}

export class UnknownCurrency extends Schema.TaggedError<UnknownCurrency>()("UnknownCurrency", {
  code: Schema.String
}) {}

export class InvalidResponse extends Schema.TaggedError<InvalidResponse>()("InvalidResponse", {}) {}

export class RatesUnavailable extends Schema.TaggedError<RatesUnavailable>()("RatesUnavailable", {
  message: Schema.String
}) {}

// Rates API as a service. The HTTP client, base URL and retry policy live in the layer.
export class Rates extends Context.Service<Rates, {
  readonly latest: (base: string) => Effect.Effect<RatesBody, InvalidResponse | RatesUnavailable>
}>()("fx-cli/Rates") {
  static readonly layer = Layer.effect(
    Rates,
    Effect.gen(function*() {
      const baseUrl = yield* Config.String("RATES_URL").pipe(
        // A missing RATES_URL is an "other failure" for the CLI.
        Effect.mapError((error) => new RatesUnavailable({ message: error.message }))
      )
      const client = (yield* HttpClient.HttpClient).pipe(HttpClient.filterStatusOk)

      // Network errors and 5xx responses are transient. Everything else (4xx, bad
      // URL, ...) fails immediately.
      const isTransient = (error: HttpClientError.HttpClientError): boolean => {
        const reason = error.reason
        return reason._tag === "TransportError" ||
          (reason._tag === "StatusCodeError" && reason.response.status >= 500)
      }

      const latest = Effect.fn("Rates.latest")(function*(base: string) {
        const url = `${baseUrl}/rates/${encodeURIComponent(base)}`
        const response = yield* client.get(url).pipe(
          Effect.retry({
            while: isTransient,
            schedule: Schedule.exponential(50),
            times: 3
          }),
          Effect.mapError((error) => new RatesUnavailable({ message: error.message }))
        )
        // Body read and Schema validation: any failure here means a bad body.
        return yield* HttpClientResponse.schemaBodyJson(RatesBody)(response).pipe(
          Effect.mapError(() => new InvalidResponse({}))
        )
      })

      return Rates.of({ latest })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}

const program = Effect.gen(function*() {
  const [base, quote] = process.argv.slice(2)
  if (base === undefined || quote === undefined) {
    return yield* new UsageError({ message: "usage: npx tsx src/main.ts <BASE> <QUOTE>" })
  }

  const rates = yield* Rates
  const body = yield* rates.latest(base)

  if (!Object.hasOwn(body.rates, quote)) {
    return yield* new UnknownCurrency({ code: quote })
  }

  const rate = body.rates[quote]
  console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
})

const exitCodeOf = (error: UsageError | UnknownCurrency | InvalidResponse | RatesUnavailable): number => {
  switch (error._tag) {
    case "UnknownCurrency":
      return 1
    case "InvalidResponse":
      return 2
    case "UsageError":
    case "RatesUnavailable":
      return 3
  }
}

const messageOf = (error: UsageError | UnknownCurrency | InvalidResponse | RatesUnavailable): string => {
  switch (error._tag) {
    case "UnknownCurrency":
      return `unknown currency: ${error.code}`
    case "InvalidResponse":
      return "invalid response"
    case "UsageError":
      return error.message
    case "RatesUnavailable":
      return `error: ${error.message}`
  }
}

const cli = program.pipe(
  // Provide before catching, so layer failures (e.g. missing RATES_URL) are handled too.
  Effect.provide(Rates.layer),
  Effect.as(0),
  Effect.catch((error) =>
    Effect.sync(() => {
      console.error(messageOf(error))
      return exitCodeOf(error)
    })
  )
)

Effect.runPromise(cli).then(
  (code) => {
    process.exitCode = code
  },
  (defect) => {
    console.error("error: unexpected failure", defect)
    process.exitCode = 3
  }
)
