# Answer: offline hbar transfer signer

## What was done

1. **SDK added under its current name.** `npm install @hiero-ledger/sdk` installed
   **2.91.0**, recorded as `"@hiero-ledger/sdk": "^2.91.0"` in `package.json`.
   The project does not use `@hashgraph/sdk`.
2. **`src/transfer.ts` written.** Run it with `npx tsx src/transfer.ts`. It:
   - loads `.env` with dotenv (`quiet: true`, so no banner goes to stdout) and reads
     `OPERATOR_ID`, `OPERATOR_KEY` (DER hex, parsed with `PrivateKey.fromStringDer`),
     `RECIPIENT_ID`, and `VALID_START` (Unix seconds). It exits with an error if any is
     missing, or if `VALID_START` is not a non-negative integer;
   - builds a `TransferTransaction`: operator −1 ℏ, recipient +1 ℏ, memo `invoice 42`,
     node `0.0.3`, and transaction ID `TransactionId.withValidStart(operator, VALID_START)`;
   - calls `freezeWith(null)` (safe because node and transaction ID are already set, so no
     client is needed), signs with the operator key, and prints `toBytes()` as hex.
   Nothing is submitted; no client or network call is made.

## Verification

- `npx tsc --noEmit` passes.
- `npx tsx src/transfer.ts` prints one line of hex (180 bytes), with no other output.
- Decoding the output with the SDK gives transaction ID `0.0.1001@1793000000`, memo
  `invoice 42`, node `0.0.3`, and transfers `0.0.1001 -1 ℏ` / `0.0.1002 1 ℏ`.
- The single signature is an ed25519 signature by the operator public key over the
  transaction body bytes (checked with Node's crypto module).

## Colleague's note: what applied

- **Applied: the SDK moved to `@hiero-ledger/sdk`.** npm shows `@hashgraph/sdk` at 2.81.0,
  last modified 2026-03-13, and `@hiero-ledger/sdk` at 2.91.0, published 2026-11-09. So
  the current SDK is the Hiero name, and I installed that one.
- **Applied: the class and method names are the same** (`TransferTransaction`,
  `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`). Only the
  import path changes.
- **Applied: verify steps.** `npm ls @hiero-ledger/sdk` shows 2.91.0, `npm ls @hashgraph/sdk`
  shows nothing, `tsc --noEmit` passes, and the output decodes to the expected transaction.
- **Did not apply: step 3 (replacing an existing `@hashgraph/sdk`).** The project had no
  Hedera SDK before this task, so there was nothing to replace.
- **Did not apply: the Node 20 prerequisite and the release-cadence note.** They don't change
  what was built. This environment runs Node 26.

## Notes

- `package-lock.json` was created by `npm install`. `node_modules/` is not ignored by git
  (the repo has no `.gitignore`); you may want to add one before committing.
- The existing `src/index.ts` was left unchanged. It isn't used by the transfer script.
- The `.env` values are test values. The script was run against them; nothing was submitted.
- Nothing was committed or pushed.
