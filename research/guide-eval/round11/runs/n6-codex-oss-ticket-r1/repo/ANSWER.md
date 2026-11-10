This file records the steps taken to satisfy the request.

## Changes Made

1. **Added the current Hedera SDK** – The project now depends on `@hiero-ledger/sdk@2.91.0`. The colleague’s note warned that the SDK moved from `@hashgraph/sdk` to `@hiero-ledger/sdk`; we followed that guidance.
2. **Created `src/transfer.ts** – A TypeScript program that:
   - Loads `.env` values (`OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID`, `VALID_START`).
   - Builds a `TransactionId` with `VALID_START` as the Unix‑seconds valid start.
   - Constructs a `TransferTransaction` sending 1 hbar from the operator to the recipient, memo `invoice 42`, targeting node `0.0.3`.
   - Signs the transaction with the operator’s DER‑encoded ED25519 private key.
   - Prints only the signed transaction bytes in hex.
   - Works entirely offline – no network submission.
3. **Verified TypeScript compilation** – `npx tsc --noEmit` succeeds with no errors.

## Parts of the colleague’s note that applied

* The SDK name change to `@hiero-ledger/sdk` was required.
* The API (imports, class names, and method signatures) remained unchanged, allowing us to keep the same transaction‑building logic.

## Running the script

```bash
# Install dependencies (already present)
npm install

# Ensure .env contains the test values (already provided)
npx tsx src/transfer.ts
```

The output is a hex string containing the signed transaction bytes.

