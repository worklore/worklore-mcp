**What was done**
- Added `@hiero-ledger/sdk` (the current Hedera‑style JavaScript SDK) to `package.json` and installed it.
- Created `src/transfer.ts` which:
  * Loads environment variables via `dotenv`.
  * Parses `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID`, and `VALID_START`.
  * Builds an offline `TransferTransaction` sending 1 hbar from the operator to the recipient, targeting node `0.0.3`, with memo `invoice 42` and a custom `TransactionId` whose valid start is the supplied Unix seconds.
  * Signs the transaction with the operator's ED25519 private key.
  * Prints the signed transaction bytes as a hex string.

**How the colleague’s note applied**
- Followed the advice to use the *current* SDK package name `@hiero-ledger/sdk` (the note explained that `@hashgraph/sdk` is outdated).
- No other parts of the note were needed; the script mirrors the described workflow but targets the correct package.

**Verification**
- Running `npm install` succeeded and added the SDK.
- `npx tsc --noEmit` passes with no TypeScript errors.
- Executing `npx tsx src/transfer.ts` prints a hex string representing the signed transaction (offline, no network call).

The project now meets the requested requirements.
