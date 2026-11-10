# Offline Hedera transfer

Installed the current npm release of the Hedera JavaScript SDK, `@hiero-ledger/sdk` 2.91.0, and added `src/transfer.ts`. The script loads `.env`, builds a 1 hbar transfer from `OPERATOR_ID` to `RECIPIENT_ID` with memo `invoice 42`, node `0.0.3`, and an operator transaction ID starting at `VALID_START` Unix seconds. It signs with the DER-encoded Ed25519 `OPERATOR_KEY` and writes only the signed transaction bytes as hex. It does not create a client or submit the transaction.

Run: `npx tsx src/transfer.ts`

Verified: `npx tsc --noEmit` passes, and the script produces a single hex line with the test `.env` values.

The colleague's package-rename note applied: `@hiero-ledger/sdk` is newer than `@hashgraph/sdk` on npm, and its named APIs support this offline flow. The note's old-package replacement step did not apply because this project had no Hedera SDK dependency or imports before the change.
