import { HttpClient, HttpClientError, HttpClientResponse, FetchHttpClient } from "effect/http";
import { Context, Duration, Effect, Layer, Schedule, Schema } from "effect";

// 1. Schema for rates response: { base: string, date: string, rates: { [code: string]: number } }
export const RatesResponse = Schema.Struct({
  base: Schema.String,
  date: Schema.String,
  rates: Schema.Record(Schema.String, Schema.Number),
});

export type RatesResponse = typeof RatesResponse.Type;

// Domain errors
export class UnknownCurrencyError {
  readonly _tag = "UnknownCurrencyError";
  constructor(readonly currency: string) {}
}

export class InvalidResponseError {
  readonly _tag = "InvalidResponseError";
  constructor(readonly cause?: unknown) {}
}

// 2. Service definition
export class RatesService extends Context.Service<
  RatesService,
  {
    readonly getRates: (
      base: string
    ) => Effect.Effect<RatesResponse, InvalidResponseError | unknown>;
  }
>()("RatesService") {}

// 3. Service Layer
export const makeRatesServiceLive = (rawBaseUrl?: string) =>
  Layer.effect(
    RatesService,
    Effect.gen(function* () {
      if (!rawBaseUrl) {
        return yield* Effect.die(new Error("RATES_URL environment variable is not defined"));
      }

      const client = yield* HttpClient.HttpClient;
      const baseUrl = rawBaseUrl.replace(/\/+$/, "");

      const isTransient = (err: unknown): boolean => {
        if (HttpClientError.isHttpClientError(err)) {
          if (err.reason._tag === "TransportError") return true;
          if (err.reason._tag === "StatusCodeError") {
            const status = err.reason.response.status;
            return status >= 500 && status < 600;
          }
        }
        return false;
      };

      const retryClient = HttpClient.retry(
        HttpClient.filterStatusOk(client),
        {
          schedule: Schedule.exponential(Duration.millis(50)),
          times: 3,
          while: isTransient,
        }
      );

      return {
        getRates: (base: string) =>
          Effect.gen(function* () {
            const url = `${baseUrl}/rates/${encodeURIComponent(base)}`;
            const response = yield* retryClient.get(url);
            const decode = HttpClientResponse.schemaBodyJson(RatesResponse);
            return yield* decode(response).pipe(
              Effect.mapError((err) => new InvalidResponseError(err))
            );
          }),
      };
    })
  );

export const RatesServiceLive = makeRatesServiceLive(process.env.RATES_URL).pipe(
  Layer.provide(FetchHttpClient.layer)
);

// 4. CLI application logic
const [base, quote] = process.argv.slice(2);

const program = Effect.gen(function* () {
  if (!base || !quote) {
    return yield* Effect.fail(new Error("Usage: npx tsx src/main.ts <BASE> <QUOTE>"));
  }

  const ratesService = yield* RatesService;
  const data = yield* ratesService.getRates(base);

  const rate = data.rates[quote];
  if (rate === undefined || typeof rate !== "number" || Number.isNaN(rate)) {
    return yield* Effect.fail(new UnknownCurrencyError(quote));
  }

  console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`);
});

const isInvalidResponse = (error: unknown): boolean => {
  if (error instanceof InvalidResponseError || (typeof error === "object" && error !== null && (error as any)._tag === "InvalidResponseError")) {
    return true;
  }
  if (Schema.isSchemaError(error)) {
    return true;
  }
  if (HttpClientError.isHttpClientError(error) && error.reason._tag === "DecodeError") {
    return true;
  }
  return false;
};

Effect.runPromiseExit(
  program.pipe(Effect.provide(RatesServiceLive))
).then((exit) => {
  if (exit._tag === "Success") {
    process.exit(0);
  }

  // Handle failure causes
  for (const reason of exit.cause.reasons) {
    if (reason._tag === "Fail") {
      const err = reason.error;
      if (err instanceof UnknownCurrencyError || (typeof err === "object" && err !== null && (err as any)._tag === "UnknownCurrencyError")) {
        console.error(`unknown currency: ${(err as UnknownCurrencyError).currency}`);
        process.exit(1);
      }
      if (isInvalidResponse(err)) {
        console.error("invalid response");
        process.exit(2);
      }
    } else if (reason._tag === "Die") {
      if (isInvalidResponse(reason.defect)) {
        console.error("invalid response");
        process.exit(2);
      }
    }
  }

  process.exit(3);
});
