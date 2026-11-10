# Answer

## What was done

- Added the Hedera JavaScript SDK at its current npm version: `@hashgraph/sdk@^2.81.0` (2.81.0 was the latest on npm when checked). Installed with `npm install`, which also created `package-lock.json`.
- Wrote `src/transfer.ts`. Run it with `npx tsx src/transfer.ts`.

## How `src/transfer.ts` works

1. Loads `.env` via `dotenv/config`, then reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 hex, parsed with `PrivateKey.fromStringDer`), `RECIPIENT_ID` and `VALID_START` (Unix seconds). Missing or invalid values throw an error.
2. Builds a `TransferTransaction`:
   - operator (`OPERATOR_ID`) sends −1 hbar, recipient (`RECIPIENT_ID`) receives +1 hbar;
   - memo `invoice 42`;
   - node account `0.0.3`;
   - transaction ID `TransactionId.withValidStart(operatorId, new Timestamp(VALID_START, 0))`.
3. Freezes with `freezeWith(null)` (no client, so no network access), signs with the operator key, and prints the bytes as lowercase hex to stdout. Nothing else is printed to stdout.

Nothing is submitted to any network.

## Verification

- `npx tsc --noEmit` passes with no errors.
- `npx tsx src/transfer.ts` exits 0 and prints a 409-byte hex string with the test `.env` values.
- Decoding the output with `Transaction.fromBytes` gives:
  - transaction ID `0.0.1001@1793000000.000000000`;
  - node `0.0.3`;
  - memo `invoice 42`;
  - transfers `0.0.1001 -1 ℏ` and `0.0.1002 +1 ℏ`;
  - one signature, which verifies against the public key derived from `OPERATOR_KEY` over the body bytes.

## Notes

- `Hbar.from` in this SDK version requires an explicit unit, so the script passes `HbarUnit.Hbar`.
- `src/index.ts` was left untouched.
- `.env` contains a private key and is not in `.gitignore`, and it is tracked in the repository's base commit. This was not changed. Consider adding `.env` to `.gitignore` and rotating the key if it was ever a real one.
- Nothing was committed, pushed or published.
