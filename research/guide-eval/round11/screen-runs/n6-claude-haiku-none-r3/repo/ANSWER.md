# Answer: offline hbar transfer signing

## What was done

1. **SDK added.** `@hashgraph/sdk` was installed at the current npm version, `2.81.0`, and recorded as a dependency in `package.json`. A `package-lock.json` was created by `npm install`.

2. **`src/transfer.ts` written.** Run with `npx tsx src/transfer.ts`. It:
   - loads `.env` via `dotenv/config`, then reads `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID` and `VALID_START`. A missing variable is reported by name and exits with code 1.
   - parses `OPERATOR_KEY` as an ED25519 DER-encoded private key (`PrivateKey.fromStringED25519`).
   - treats `VALID_START` as Unix seconds and requires a non-negative integer.
   - builds a `TransferTransaction` that debits 1 hbar from the operator and credits 1 hbar to the recipient.
   - sets the memo to `invoice 42`, built from `TREASURY_MEMO_PREFIX` exported by the existing `src/index.ts`.
   - sets the node account to `0.0.3`.
   - sets the transaction ID to `TransactionId.withValidStart(operatorId, VALID_START)`.
   - freezes the transaction locally, signs it with the operator key, and prints `toBytes()` as lowercase hex to stdout.

   Nothing is submitted. No network client is created, so the script works offline.

## Verification

- `npx tsc --noEmit` passes with exit code 0.
- `npx tsx src/transfer.ts` with the `.env` test values exits 0 and prints one hex line.
- The output was decoded offline with `Transaction.fromBytes`. Results:
  - memo: `invoice 42`
  - transaction ID: `0.0.1001@1793000000.000000000`
  - node: `0.0.3`
  - transfers: `0.0.1001 -100000000` and `0.0.1002 +100000000` tinybars (1 hbar)
- The signature was checked against the operator's public key. The public key in the signature pair matches the operator key, and the ED25519 signature verifies over the body bytes.

## Notes

- `.env` is tracked in git, and the repo has no `.gitignore`. The file holds an operator private key, even though these are test values. Consider adding `.env` to `.gitignore` and removing it from the index before this repo gets real keys. I did not change this.
- I did not commit anything.
