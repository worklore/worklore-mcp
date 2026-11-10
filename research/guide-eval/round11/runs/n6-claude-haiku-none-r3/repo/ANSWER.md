# Hedera transfer signing: what was done

## Dependencies

- Added `@hashgraph/sdk@2.81.0` (the latest version on npm at the time of the check) as a dependency. `npm install` also installed the existing `dotenv`, `tsx`, `typescript` and `@types/node` dependencies.

## `src/transfer.ts`

Run with `npx tsx src/transfer.ts` (also available as `npm run transfer`).

1. Loads `.env` via `dotenv/config`, then reads `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID` and `VALID_START`. A missing variable, or a `VALID_START` that is not a non-negative integer, throws an error.
2. `OPERATOR_KEY` is parsed with `PrivateKey.fromStringDer` (DER-encoded hex).
3. Builds a `TransferTransaction`:
   - operator debited 1 hbar (-100,000,000 tinybars), recipient credited 1 hbar;
   - memo `invoice 42`;
   - node account `0.0.3`;
   - transaction ID `TransactionId.withValidStart(operatorId, new Timestamp(VALID_START, 0))`, so the valid start is `VALID_START` seconds.
4. Freezes the transaction, signs it with the operator key (`await tx.sign(...)`), and prints the signed bytes as lowercase hex. Nothing else is printed.

No network calls are made: the transaction is frozen with an explicit node and transaction ID, so no client or consensus node is needed.

## Verification

- `npx tsc --noEmit` passes with no errors.
- `npx tsx src/transfer.ts` exits 0 and prints a hex string.
- The output was decoded offline with `Transaction.fromBytes`. It gave memo `invoice 42`, node `0.0.3`, transaction ID `0.0.1001@1793000000.000000000`, and transfers `0.0.1001 = -100000000` and `0.0.1002 = +100000000`.
- The signature was not independently verified against the public key beyond the SDK's signing call.

## Notes

- The `.env` test values were used as-is, and the output is for those values only. Nothing was submitted or sent anywhere.
- `node_modules/` and `package-lock.json` were created by the install. There is no `.gitignore` in the repo, so `node_modules/` will show up in `git status`. Nothing was committed.
- `src/index.ts` was left unchanged.
