# Summary

## What I did

1. **Added the Hedera JavaScript SDK**: Installed `@hiero-ledger/sdk@2.91.0` (the current package name for the Hedera SDK, which moved from `@hashgraph/sdk` as noted in the colleague's note).

2. **Created `src/transfer.ts`**: A TypeScript script that:
   - Reads `OPERATOR_ID`, `OPERATOR_KEY` (ED25519 private key, DER-encoded hex), `RECIPIENT_ID`, and `VALID_START` (Unix seconds) from the environment via `dotenv`
   - Builds a transfer transaction of 1 hbar from operator to recipient
   - Sets the memo to `invoice 42`
   - Sets node account to `0.0.3`
   - Creates a transaction ID for the operator with the specified valid start time
   - Freezes and signs the transaction with the operator key
   - Prints the signed transaction bytes as hex

3. **Verified**: 
   - `npx tsc --noEmit` passes with no errors
   - `npx tsx src/transfer.ts` runs successfully and outputs the signed transaction bytes

## Colleague's note applicability

The colleague's note **applied** in the following ways:

- **Package name**: The SDK has indeed moved from `@hashgraph/sdk` to `@hiero-ledger/sdk`. I used the new package name `@hiero-ledger/sdk` (version 2.91.0).
- **API compatibility**: The class names and methods mentioned in the note (`TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`) all work the same way in the new package.
- **Memo field**: The note didn't mention it, but I discovered that `setTransactionMemo` is the correct method (not `setMemo`).

The note **did not apply** in:
- The old `@hashgraph/sdk` package is not needed or used.

## Implementation details

- Used `Timestamp.fromDate()` to convert Unix seconds to a Timestamp object
- Used `transaction.freeze()` before signing (required by the SDK)
- Used `toBytes()` method which exists at runtime but is not in the TypeScript type definitions (the types only expose `toBytesAsync()`). A type assertion to `any` was used to access it.
- The output is a single line of hex-encoded signed transaction bytes.
