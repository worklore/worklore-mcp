# Implementation Summary

## What I did

1. **Added the Hedera JavaScript SDK**: Added `@hiero-ledger/sdk` (version ^2.90.0) as a dependency in `package.json`. This is the current package name for the Hedera SDK, as the colleague's note correctly identified that the SDK moved from `@hashgraph/sdk` to `@hiero-ledger/sdk`.

2. **Wrote `src/transfer.ts`**: Created a TypeScript script that:
   - Loads environment variables from `.env` using `dotenv`
   - Reads `OPERATOR_ID`, `OPERATOR_KEY` (ED25519 private key, DER-encoded hex), `RECIPIENT_ID`, and `VALID_START` (Unix seconds)
   - Builds a transfer transaction of 1 hbar from operator to recipient
   - Sets the transaction memo to `invoice 42`
   - Sets the node account ID to `0.0.3`
   - Creates a transaction ID for the operator with the specified valid start time (converted to a `Timestamp` object)
   - Freezes the transaction and signs it with the operator key
   - Outputs the signed transaction bytes as hex

3. **Verified the implementation**:
   - `npx tsx src/transfer.ts` runs successfully and outputs the signed transaction bytes as hex
   - `npx tsc --noEmit` passes TypeScript type checking

## What applied from the colleague's note

The colleague's note was directly relevant:

- **Package name**: The note correctly states that the current Hedera JavaScript SDK is `@hiero-ledger/sdk` (2.90+), not `@hashgraph/sdk` (which stopped at 2.81.0). I used `@hiero-ledger/sdk` as the dependency.

- **API compatibility**: The note confirms that "the same imports and calls work in both packages" - `TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar` all work the same way in the new package.

- **Offline operation**: The note's focus on offline transaction building and signing aligned with the requirement to work offline without submitting to any network.

What did not apply:
- The note's reproduction steps and checks were not needed since I was starting from a clean project.
- The note's ground rules about not deploying/publishing were already consistent with the task requirements.
