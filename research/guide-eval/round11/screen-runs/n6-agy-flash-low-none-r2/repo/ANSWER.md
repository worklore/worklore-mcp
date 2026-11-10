# Hedera Transfer Implementation

## Summary of Changes

1. **Installed Hedera JavaScript SDK**:
   - Added `@hashgraph/sdk` to `package.json` dependencies using `npm install @hashgraph/sdk`.

2. **Created `src/transfer.ts`**:
   - Reads environment variables via `dotenv/config`: `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID`, and `VALID_START`.
   - Parses the operator private key using `PrivateKey.fromStringED25519()`.
   - Constructs a `Timestamp(validStartSeconds, 0)` and a `TransactionId(operatorId, validStart)`.
   - Configures node account ID `0.0.3` via `.setNodeAccountIds([AccountId.fromString("0.0.3")])`.
   - Builds a transfer of 1 Hbar from the operator account (`-1`) to the recipient account (`+1`) via `TransferTransaction`.
   - Sets the transaction memo to `"invoice 42"`.
   - Freezes the transaction offline without connecting to any network.
   - Signs the transaction with the operator's private key.
   - Serializes the signed transaction bytes to hex and outputs only the hex string to standard output.

3. **Verification**:
   - Checked TypeScript compilation using `npx tsc --noEmit` (passed without errors).
   - Executed `npx tsx src/transfer.ts` and verified transaction fields, signature mapping, and offline hex output.
