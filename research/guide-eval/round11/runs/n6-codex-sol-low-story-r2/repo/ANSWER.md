# Offline Hedera transfer

Installed the current npm release of `@hiero-ledger/sdk` (2.91.0). Added `src/transfer.ts`, which reads the four environment variables, builds a 1 hbar transfer with memo `invoice 42` for node `0.0.3`, sets the operator's transaction ID to `VALID_START`, signs it with the DER encoded ED25519 key, and prints only the signed transaction bytes in hex. It freezes and signs locally; it does not submit the transaction.

Run with `npx tsx src/transfer.ts`. Type checking passes with `npx tsc --noEmit`.

The colleague's note applied: the current SDK is published as `@hiero-ledger/sdk`, while `@hashgraph/sdk` is older. Its suggested SDK classes and `PrivateKey.fromStringDer` were used. Its replacement step did not apply because this project had no existing Hedera SDK dependency.
