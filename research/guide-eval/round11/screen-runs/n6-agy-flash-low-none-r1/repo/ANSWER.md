# Hedera Transfer Implementation

## Summary of Changes

1. **Installed Hedera JavaScript SDK**:
   - Added `@hashgraph/sdk` (`^2.81.0`) to `package.json` dependencies via npm.

2. **Implemented `src/transfer.ts`**:
   - Loads environment variables using `dotenv/config`:
     - `OPERATOR_ID`: Sender Hedera account ID.
     - `OPERATOR_KEY`: DER-encoded hex ED25519 private key, parsed using `PrivateKey.fromStringED25519`.
     - `RECIPIENT_ID`: Recipient Hedera account ID.
     - `VALID_START`: Unix timestamp in seconds, used to construct `Timestamp(validStartSec, 0)` and `TransactionId.withValidStart`.
   - Constructs an offline `TransferTransaction`:
     - Sets transaction ID to `0.0.1001@VALID_START.000000000`.
     - Sets node account ID to `0.0.3`.
     - Transfers `-1 Hbar` from the operator and `+1 Hbar` to the recipient.
     - Sets transaction memo to `invoice 42`.
   - Freezes and signs the transaction offline using the operator private key.
   - Serializes the signed transaction to bytes via `transaction.toBytes()` and prints only the hex-encoded string.

3. **Verification**:
   - Passed TypeScript type checking with `npx tsc --noEmit`.
   - Executed `npx tsx src/transfer.ts` and verified the output format and transaction fields offline.
