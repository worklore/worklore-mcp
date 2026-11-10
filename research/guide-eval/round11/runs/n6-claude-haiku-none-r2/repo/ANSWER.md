# Answer

## What was done

1. **SDK added:** `@hashgraph/sdk@2.81.0`, the current npm `latest` version at the time of work, installed as a dependency with `npm install @hashgraph/sdk@2.81.0`.

2. **`src/transfer.ts` written.** Run with `npx tsx src/transfer.ts` (or `npm run transfer`). It:
   - loads `.env` via `dotenv/config`. `dotenv` is already a project dependency.
   - reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 private key, hex, parsed with `PrivateKey.fromStringDer`), `RECIPIENT_ID` and `VALID_START` (Unix seconds). Missing variables and a non-integer `VALID_START` raise an error.
   - builds a `TransferTransaction` that debits the operator 1 hbar and credits the recipient 1 hbar.
   - sets the memo to `invoice 42`. The `invoice` prefix is taken from the existing `TREASURY_MEMO_PREFIX` export in `src/index.ts`.
   - sets node account `0.0.3`.
   - sets the transaction ID to `TransactionId.withValidStart(operatorId, Timestamp(VALID_START, 0))`.
   - freezes the transaction, signs it with the operator key, and prints `toBytes()` as lowercase hex.
   - makes no network calls. Nothing is submitted.

3. **Verified:**
   - `npx tsc --noEmit` passes with exit code 0.
   - `npx tsx src/transfer.ts` exits 0, prints a single line of hex, and writes nothing to stderr.
   - Two runs produce identical output, so the output is deterministic.
   - Decoding the output with the SDK's `Transaction.fromBytes` gives:
     - memo `invoice 42`
     - transaction ID `0.0.1001@1793000000.000000000`
     - node `0.0.3`
     - transfers `0.0.1001: -1 ℏ` and `0.0.1002: +1 ℏ`
     - one signature

## Choices made

- `VALID_START` is used as whole seconds with zero nanoseconds.
- The script reads `.env` through `import "dotenv/config"`. In the test run, stdout contained only the hex line, so no dotenv log line was printed.

## Notes for the user

- `.env` contains an operator private key and there is no `.gitignore`. Add a `.gitignore` that excludes `.env` and `node_modules` before committing. Nothing was committed.
- The `OPERATOR_KEY` in `.env` is labelled as a test value. The script never sends the key anywhere.
