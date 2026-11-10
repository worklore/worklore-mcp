# Summary of Changes

## What I Did

1. **Installed the correct Hedera SDK**: Based on the colleague's note, I installed `@hiero-ledger/sdk` (version 2.91.0) instead of the deprecated `@hashgraph/sdk` (which stopped at 2.81.0). The colleague's note was accurate - the SDK had moved to `@hiero-ledger/sdk` with new releases, while `@hashgraph/sdk` was no longer maintained despite npm still marking it as `latest`.

2. **Created `src/transfer.ts`**: The script:
   - Reads environment variables: `OPERATOR_ID`, `OPERATOR_KEY` (ED25519 private key, DER-encoded hex), `RECIPIENT_ID`, and `VALID_START` (Unix seconds)
   - Builds a transfer transaction of 1 hbar from operator to recipient
   - Sets memo to `invoice 42`
   - Targets node `0.0.3`
   - Uses a transaction ID for the operator with the specified valid start time
   - Signs with the operator key
   - Prints only the signed transaction bytes as hex
   - Works completely offline (no network submission)

3. **Key implementation details**:
   - Used `PrivateKey.fromStringDer()` to parse the DER-encoded hex private key
   - Used `TransactionId.withValidStart()` with a `Timestamp` object (seconds, nanos)
   - Used `setTransactionMemo()` instead of `setMemo()` (the correct method name in the SDK)
   - Used `signWith()` with the public key and a signing function
   - Called `freeze()` before signing to ensure the transaction hash is stable
   - Converted the bytes to hex using `Buffer.from(bytes).toString("hex")`

4. **Verified TypeScript compilation**: The project passes `npx tsc --noEmit` with no errors.

5. **Tested execution**: The script runs successfully with `npx tsx src/transfer.ts` and outputs the signed transaction bytes as hex.

## What Applied from the Colleague's Note

The following parts of the colleague's note were relevant and applied:

- The SDK package name changed from `@hashgraph/sdk` to `@hiero-ledger/sdk`
- Version 2.81.0 was the last for `@hashgraph/sdk` (released 2026-03-13)
- `@hiero-ledger/sdk` continues with versions 2.90+ and receives new releases
- The class names and method calls remain the same: `TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`
- The fix required only changing the dependency and import path

The note's investigation into comparing release dates and checking `npm view @hashgraph/sdk version` was helpful context, though I verified the current package directly.

## Files Modified

- `package.json`: Added `@hiero-ledger/sdk` dependency
- `src/transfer.ts`: Created new file with the transfer logic
- `ANSWER.md`: This summary file

## Files Unchanged

- `.env`: Already contained test values
- `tsconfig.json`: Already configured correctly
- `src/index.ts`: Left unchanged as it was not part of the task
