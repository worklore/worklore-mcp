Added Hedera SDK and offline transfer script.

**Changes made**
- Installed `@hiero-ledger/sdk` (the current Hedera SDK) and `dotenv`.
- Created a `.env` with test values for `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID`, `VALID_START`.
- Added `src/transfer.ts` that:
  * Loads env vars via `import "dotenv/config"`.
  * Builds `AccountId`, `PrivateKey`, `Timestamp` (from Unix seconds) and a `TransactionId`.
  * Creates a `TransferTransaction` moving 1 hbar from operator to recipient, memo `invoice 42`, node `0.0.3`.
  * Freezes, signs with the operator key, and outputs the signed bytes as hex.
  * Compiles cleanly (`npx tsc --noEmit` succeeds).

**Colleague note applied**
- Adopted the renamed package `@hiero-ledger/sdk` as described.
- No other code changes were needed because the SDK API is unchanged.

**How to run**
```bash
npx tsx src/transfer.ts
```
The script prints only the hex‑encoded signed transaction.

Replace the placeholder values in `.env` with real credentials to produce a valid signed transaction for testing.
