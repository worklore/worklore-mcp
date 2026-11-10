# Hedera Offline Transfer Implementation

## Summary of Changes
1. **Installed Hedera JavaScript SDK**:
   - Added `@hashgraph/sdk` from npm to `package.json` dependencies using `npm install @hashgraph/sdk`.

2. **Created `src/transfer.ts`**:
   - Imported required classes (`AccountId`, `PrivateKey`, `Timestamp`, `TransactionId`, `TransferTransaction`, `Hbar`) from `@hashgraph/sdk`, and loaded environment variables via `dotenv/config`.
   - Read and validated required environment variables:
     - `OPERATOR_ID`: Hedera account ID of the operator (`0.0.1001`).
     - `OPERATOR_KEY`: DER-encoded ED25519 private key hex string, parsed with `PrivateKey.fromStringED25519(...)`.
     - `RECIPIENT_ID`: Hedera account ID of the recipient (`0.0.1002`).
     - `VALID_START`: Unix timestamp in seconds, used to initialize a `Timestamp` and construct a `TransactionId.withValidStart(operatorId, validStart)`.
   - Built a `TransferTransaction`:
     - Configured transaction ID with operator and valid start time.
     - Set node account ID to `0.0.3` via `.setNodeAccountIds([AccountId.fromString("0.0.3")])`.
     - Added debit of 1 hbar (`new Hbar(-1)`) to operator and credit of 1 hbar (`new Hbar(1)`) to recipient.
     - Added memo `"invoice 42"`.
     - Froze transaction with `.freeze()` without client submission/network communication.
   - Signed transaction with `await transaction.sign(operatorKey)`.
   - Exported signed transaction bytes via `signedTx.toBytes()` and printed only the hex-encoded string to standard output.

3. **Verification**:
   - Passed TypeScript type checks cleanly via `npx tsc --noEmit`.
   - Verified execution via `npx tsx src/transfer.ts` and `npm run transfer`, outputting only the signed transaction hex bytes.
