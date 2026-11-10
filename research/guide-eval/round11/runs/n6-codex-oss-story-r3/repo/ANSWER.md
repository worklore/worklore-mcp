Implemented the requested offline Hedera transfer script.

### What was done
* Added **@hiero-ledger/sdk** (the current Hedera JavaScript SDK) to `package.json`.
* Created a `.env` file with placeholder test values for the required environment variables.
* Added `src/transfer.ts` that:
  - Loads environment variables via `dotenv`.
  - Parses `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID`, and `VALID_START`.
  - Builds a `TransferTransaction` transferring **1 hbar** from the operator to the recipient, using node `0.0.3` and memo `invoice 42`.
  - Uses `Timestamp.fromDate` to create the correct `Timestamp` type for `TransactionId.withValidStart`.
  - Freezes, signs with the operator’s ED25519 DER‑encoded key, and prints the signed transaction bytes as a hex string.
  - Runs offline – no network calls are made.
* Confirmed the code compiles with `npx tsc --noEmit`.

### Parts of the colleague’s note that applied
* The note highlighted that the SDK has moved to `@hiero-ledger/sdk`. This guided the choice of dependency and import statements.
* It confirmed that the API (e.g., `TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`) remains the same, so no additional code changes were needed beyond the import path.

You can execute the script with:
```
npx tsx src/transfer.ts
```
The output will be a single hex string representing the signed transaction.

