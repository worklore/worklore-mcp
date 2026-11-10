# Answer: offline Hedera transfer signer

## What was done

1. **SDK added.** `@hashgraph/sdk` version `2.81.0` (the current npm `latest` at the time of the work) was installed with `npm install @hashgraph/sdk@2.81.0`. `package.json` and `package-lock.json` were updated.

2. **`src/transfer.ts` written.** Run with `npx tsx src/transfer.ts`. It:
   - reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 private key, hex, parsed with `PrivateKey.fromStringDer`), `RECIPIENT_ID` and `VALID_START` (Unix seconds) from the environment; `.env` is loaded through `dotenv/config`;
   - builds a `TransferTransaction` moving 1 hbar (100,000,000 tinybars) from the operator to the recipient, with memo `invoice 42`;
   - sets node account `0.0.3`;
   - sets the transaction ID to `TransactionId.withValidStart(operatorId, new Timestamp(VALID_START, 0))`;
   - freezes locally (no client, so nothing is contacted), signs with the operator key, and prints the bytes as lowercase hex on stdout.
   - On a missing or invalid variable it prints the error to stderr and exits with status 1.

3. **Type check.** `npx tsc --noEmit` passes with no errors.

## Verification (offline)

- `npx tsx src/transfer.ts` printed one hex line and exited 0. No network calls are made: the transaction is frozen with an explicit node and transaction ID, so no client is created.
- The output was decoded again with `Transaction.fromBytes` and checked:
  - memo: `invoice 42`
  - transaction ID: `0.0.1001@1793000000.000000000`
  - node: `0.0.3`
  - transfers: `0.0.1001 → -100000000`, `0.0.1002 → +100000000` tinybars (−1 / +1 hbar)
  - one signature present on the transaction.

## Choices I made

- The hbar amount is 1 hbar exactly, expressed as `Hbar.fromTinybars(±100_000_000)`.
- `VALID_START` is validated as a non-negative integer and rejected otherwise.
- The output contains only the hex string on stdout; diagnostics go to stderr.

## Things to note

- There is no `.gitignore`, so `node_modules/` and `package-lock.json` show as untracked. I did not commit anything.
- `.env` is tracked in git and contains an operator private key. The values are test values, but the file should not be committed with real keys. Consider adding `.env` to a `.gitignore`.
- `src/index.ts` was not modified.
