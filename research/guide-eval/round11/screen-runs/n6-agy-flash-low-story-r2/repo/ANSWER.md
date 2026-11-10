# Hedera Transfer Implementation

## Actions Taken
1. **Installed Hedera JavaScript SDK**:
   - Installed `@hiero-ledger/sdk` (`^2.91.0`), which is the current package name for the Hedera JavaScript SDK on npm (replacing `@hashgraph/sdk`).
2. **Created `src/transfer.ts`**:
   - Read `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID`, and `VALID_START` from environment variables via `dotenv/config`.
   - Parsed `OPERATOR_KEY` as a DER-encoded private key using `PrivateKey.fromStringDer(...)`.
   - Constructed the `TransactionId` using `TransactionId.withValidStart(operatorId, new Timestamp(validStartSec, 0))`.
   - Built a `TransferTransaction` targeting node `0.0.3`, transferring -1 Hbar from operator and +1 Hbar to recipient, with memo `invoice 42`.
   - Froze the transaction offline (`freeze()`) and signed it with the operator key (`await transaction.sign(...)`).
   - Serialized the signed transaction to bytes and printed only the hex string representation to `stdout`.
3. **Verification**:
   - Verified that `npx tsx src/transfer.ts` outputs only the signed transaction hex.
   - Verified that `npx tsc --noEmit` completes cleanly with no TypeScript errors.

## Colleague Note Application

From the colleague's note on the package migration:
- **What applied**:
  - The SDK package rename to `@hiero-ledger/sdk`: as noted, the current SDK package is published under `@hiero-ledger/sdk` rather than the old `@hashgraph/sdk`.
  - Step 1 & 2 of the note: Installed `@hiero-ledger/sdk` directly and imported `TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, and `Hbar` from `@hiero-ledger/sdk`.
  - Verification guidance: Confirmed `@hiero-ledger/sdk` is installed (v2.91.0) and `@hashgraph/sdk` is not present.
- **What did not apply**:
  - Step 3 (replacing existing `@hashgraph/sdk` dependency and imports in the project): The project did not previously have `@hashgraph/sdk` installed, so no removal or migration was needed.
