# What I did

## SDK package
The Hedera JavaScript SDK is now published as **`@hiero-ledger/sdk`**. The project moved from the `hashgraph` GitHub org to `hiero-ledger`. The old `@hashgraph/sdk` package still exists, but its last release was 2.81.0 (2026-03-13). Both packages point to the same repo (`hiero-ledger/hiero-sdk-js`), and that README says to install `@hiero-ledger/sdk`.

- Installed `@hiero-ledger/sdk@2.91.0`, the current `latest` on npm (published 2026-11-09). `package.json` has `^2.91.0` and `package-lock.json` pins the exact version.
- npm skipped the postinstall scripts for `protobufjs` and `esbuild` (they aren't on the allowlist). Nothing needed them: `tsc` and `tsx` both work.
- Added a `.gitignore` containing `node_modules/`.

## src/transfer.ts
Run with `npx tsx src/transfer.ts` (or `npm run transfer`).

1. Loads `.env` with `dotenv` using `quiet: true`, because dotenv v17 otherwise prints a banner to stdout. Then reads `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID` and `VALID_START`. It stops with an error if any is missing, if the key isn't ED25519, or if `VALID_START` isn't an integer.
2. Parses the key with `PrivateKey.fromStringDer`.
3. Builds a `TransferTransaction`: −1 hbar from the operator, +1 hbar to the recipient, memo `invoice 42` (made from `TREASURY_MEMO_PREFIX` in `src/index.ts`), `TransactionId.withValidStart(operator, Timestamp(VALID_START, 0))`, and node `0.0.3`.
4. Calls `freeze()` without a `Client`, so nothing touches the network. This works because the transaction ID and node IDs are set explicitly.
5. Signs with the operator key and writes only the signed `Transaction` bytes as hex, on one line.

## Verification
- `npx tsc --noEmit` passes.
- I decoded the output with `Transaction.fromBytes` in a throwaway script (since deleted). It contains: memo `invoice 42`, transaction ID `0.0.1001@1793000000.000000000`, node `[0.0.3]`, transfers `0.0.1001: -100000000 tinybar` and `0.0.1002: +100000000 tinybar`, and one signature that the operator's public key verifies.
- Running it twice gives the same bytes (ED25519 signatures are deterministic).

## Notes
- No max fee is set, so the SDK default of 1 hbar is used. Add `.setMaxTransactionFee(...)` if the submitting service needs a different value.
- The test `VALID_START` (1793000000 = 2026-10-25) is in the past. A transaction ID is only valid for about 3 minutes after its valid start, so the network would reject these exact bytes as expired. That's fine for this offline build/sign step.
- Nothing was submitted, published or sent anywhere.
