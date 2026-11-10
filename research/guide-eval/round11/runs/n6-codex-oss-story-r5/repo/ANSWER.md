**Changes Made**
- Added the current Hedera JavaScript SDK `@hiero-ledger/sdk` (v2.91.0) to `package.json`.
- Created a `.env` file with example operator/recipient IDs, a DER‑encoded private key, and a valid start timestamp.
- Implemented `src/transfer.ts`:
  * Loads environment variables via `dotenv`.
  * Constructs a `TransactionId` with the supplied `VALID_START`.
  * Builds a `TransferTransaction` sending 1 hbar from the operator to the recipient, using node 0.0.3 and memo `invoice 42`.
  * Signs the transaction with the operator private key.
  * Outputs only the signed transaction bytes as a hex string.
  * Wrapped in an async IIFE so it works with `tsx` without needing explicit `await` at the top level.

**Applied Parts of the Colleague Note**
- The note warned that the SDK moved to `@hiero-ledger/sdk`; we followed that advice and used the new package.
- Imported the same classes (`TransferTransaction`, `PrivateKey`, `TransactionId`, `AccountId`, `Hbar`, `Timestamp`) because they have identical APIs in the new package.
- Used `TransactionId.withValidStart` to set the custom valid start time.
- Set the node account ID with `AccountId.fromString('0.0.3')` as recommended for a specific node.

The project now passes `npx tsc --noEmit` and `npx tsx src/transfer.ts` prints the signed transaction hex without contacting any network.
