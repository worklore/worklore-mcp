Installed the current npm release of the Hedera JavaScript SDK, `@hiero-ledger/sdk` 2.91.0, and added `src/transfer.ts`. It reads the four environment variables, builds the specified 1 hbar transfer for node 0.0.3, signs it locally, and writes only the signed transaction bytes as hex. It never submits the transaction.

The colleague's note applied to the SDK package choice: `@hiero-ledger/sdk` is newer than `@hashgraph/sdk` on npm, and the mentioned SDK classes and methods are available under the new package name. Its package migration step did not apply because this project had no existing `@hashgraph/sdk` dependency.

Verified with `npx tsc --noEmit` and `npx tsx src/transfer.ts` using the supplied `.env` values; both completed successfully.
