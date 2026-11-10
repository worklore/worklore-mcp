# Offline hbar transfer

Installed `@hiero-ledger/sdk` 2.91.0, the current npm release when checked. `src/transfer.ts` loads the provided environment values, constructs the specified one hbar transfer for node `0.0.3` with memo `invoice 42` and the supplied valid start, signs it with the DER encoded ED25519 key, and prints the signed transaction bytes as hex. It does not create a client or submit the transaction.

The colleague's note applied to choosing `@hiero-ledger/sdk` instead of the older `@hashgraph/sdk`, and to the SDK APIs for DER key parsing, transaction ID valid start, transfer construction, and signing. There was no old SDK dependency to remove in this project.

Verified with `npx tsc --noEmit` and `npx tsx src/transfer.ts`; the latter produced a single hex line (180 signed bytes) using the supplied `.env` values. No network submission was made.
