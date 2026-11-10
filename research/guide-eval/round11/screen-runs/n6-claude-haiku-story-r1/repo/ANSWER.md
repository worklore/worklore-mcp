# Answer: offline hbar transfer with the Hedera JavaScript SDK

## Which SDK package

The current Hedera JavaScript SDK is `@hiero-ledger/sdk`. I checked npm:

- `@hiero-ledger/sdk`: latest is 2.91.0 (published 2026-11-09).
- `@hashgraph/sdk`: last version is 2.81.0, modified 2026-03-13. It still reports `latest` and is not deprecated, so `npm view` alone looks normal.

I installed `@hiero-ledger/sdk@^2.91.0` and did not install `@hashgraph/sdk`. `npm ls` shows `@hiero-ledger/sdk@2.91.0` and nothing for `@hashgraph/sdk`.

## Colleague's note: what applied

- **Applied:** the package rename. I compared release dates on both names, and `@hiero-ledger/sdk` is the current one.
- **Applied:** the verify steps. `npm ls` shows a 2.9x version and no `@hashgraph/sdk`, `npx tsc --noEmit` passes, and the script's output decodes to the expected transaction (details below).
- **Not applicable:** step 3 (replacing an existing `@hashgraph/sdk`). The project did not have it.
- **Not checked:** the note's claim that both package names point at the same GitHub repo. I did not verify it.

## What `src/transfer.ts` does

1. Loads `.env` with `dotenv/config`, then reads `OPERATOR_ID`, `OPERATOR_KEY` (DER hex, via `PrivateKey.fromStringDer`), `RECIPIENT_ID` and `VALID_START`. A missing variable or a bad `VALID_START` exits with an error on stderr.
2. Builds a `TransferTransaction`: -1 hbar from the operator, +1 hbar to the recipient, memo `invoice 42`.
3. Sets node `0.0.3` and a transaction ID `TransactionId.withValidStart(operatorId, new Timestamp(VALID_START, 0))`.
4. Calls `freeze()`. No Client is created and nothing connects to a network.
5. Signs with the operator key and prints only the hex of `toBytes()` to stdout.

## Checks I ran

- `npx tsc --noEmit`: passes.
- `npx tsx src/transfer.ts`: exits 0, prints 360 hex characters, and writes nothing to stderr.
- I decoded the output with `Transaction.fromBytes` and found:
  - memo `"invoice 42"`
  - transaction ID account `0.0.1001`, valid start `1793000000` seconds, 0 nanos
  - node `0.0.3`
  - transfers `0.0.1001 = -100000000` tinybars and `0.0.1002 = +100000000` tinybars (1 hbar each way)
  - one signature, whose public key matches the operator key
  - the ED25519 signature verifies over the body bytes

The decode check was a throwaway script that I deleted afterward. Nothing was submitted to any network.

## Other changes

- `package.json` / `package-lock.json`: added `@hiero-ledger/sdk` as a dependency. The existing dependencies are unchanged.
- The project has no `.gitignore`, so `node_modules/` shows as untracked. I did not add one or commit anything.
- `src/index.ts` is unchanged.
- The SDK's `Transaction` class is not used in the script; only `TransferTransaction` and the helpers are imported.
