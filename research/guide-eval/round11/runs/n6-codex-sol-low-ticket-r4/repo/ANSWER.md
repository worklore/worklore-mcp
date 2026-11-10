# Offline hbar transfer

Installed `@hiero-ledger/sdk` 2.91.0, the current version reported by npm, and added `src/transfer.ts`. Run it with `npx tsx src/transfer.ts`. It loads the four values from `.env` or the environment, creates a 1 hbar transfer from the operator to the recipient with memo `invoice 42`, node `0.0.3`, and the supplied Unix-second valid start, then signs it with the DER-encoded ED25519 key. Standard output contains only the signed transaction bytes as hex. The script has no client or network submission call.

Verified with `npx tsc --noEmit` and an offline run of `npx tsx src/transfer.ts`; the output was one hex line.

The colleague's package-name finding applied: `@hiero-ledger/sdk` is current while `@hashgraph/sdk` remains at 2.81.0. The listed SDK classes and methods also applied. The package replacement step did not apply because this project had no Hedera SDK dependency before this change.
