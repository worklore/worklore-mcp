## Summary

Added the Hedera JavaScript SDK (`@hashgraph/sdk@^2.81.0`) to the project via npm.

Created `src/transfer.ts` that:
- Reads `OPERATOR_ID`, `OPERATOR_KEY` (ED25519 private key, DER-encoded hex), `RECIPIENT_ID`, and `VALID_START` (Unix seconds) from the environment via dotenv
- Builds a transfer transaction of 1 hbar from operator to recipient with memo `invoice 42`
- Sets node account to `0.0.3`
- Creates a transaction ID for the operator with the specified valid start time
- Freezes the transaction, signs it with the operator key, and prints the signed transaction bytes as hex
- Works completely offline without submitting to any network

The project passes `npx tsc --noEmit`.

### Changes made:
1. `npm install @hashgraph/sdk --save` - added the SDK dependency
2. Created `src/transfer.ts` with the transfer logic
3. Verified with `npx tsx src/transfer.ts` - outputs signed transaction hex
4. Verified with `npx tsc --noEmit` - TypeScript compilation succeeds
