# Offline Hedera transfer

Installed `@hiero-ledger/sdk` 2.91.0 from npm and added `src/transfer.ts`. Run it with `npx tsx src/transfer.ts`; it loads `.env`, builds a 1 hbar transfer with the requested memo, node and valid start, signs it locally with the DER encoded ED25519 key, and prints only the signed bytes as hex. It does not create a client or submit the transaction.

Verified with `npx tsc --noEmit` and decoded the script output to confirm the memo, node, transaction ID, and transfer amounts.

The colleague's package rename note applied: `@hiero-ledger/sdk` is the current package (2.91.0 on npm), while `@hashgraph/sdk` is at 2.81.0. The project did not have the old package, so no replacement or removal was needed. The note's suggested SDK classes and methods also applied.
