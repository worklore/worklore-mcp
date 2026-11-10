# Offline Hedera transfer

Added `@hashgraph/sdk` 2.81.0 from npm. `src/transfer.ts` loads the four required values from `.env`, constructs a 1 hbar transfer with memo `invoice 42`, node `0.0.3`, and the specified transaction valid start, then freezes and signs it with the DER encoded ED25519 key. It writes only the signed transaction bytes as hexadecimal to stdout and makes no network request.

Run with `npx tsx src/transfer.ts`. Type check with `npx tsc --noEmit`.
