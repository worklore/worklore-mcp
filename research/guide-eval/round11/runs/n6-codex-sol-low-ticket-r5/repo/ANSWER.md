# Offline hbar transfer

Installed `@hiero-ledger/sdk` 2.91.0, the current version reported by npm, and added `src/transfer.ts`. Run `npx tsx src/transfer.ts` with the values in `.env`; stdout contains only the signed transaction bytes as hex. The script sets the operator transaction ID and valid start, node `0.0.3`, memo `invoice 42`, and balanced 1 hbar transfers, then freezes and signs locally. It does not create a client or submit the transaction.

Verified with `npx tsc --noEmit` and a local run of `npx tsx src/transfer.ts` (one 360-character hex line).

The colleague's package-name warning applied: npm reports `@hiero-ledger/sdk` 2.91.0 and `@hashgraph/sdk` 2.81.0, so this project uses `@hiero-ledger/sdk`. The noted class names and methods also applied. The prior package migration steps did not apply because this project had no existing Hedera SDK dependency.
