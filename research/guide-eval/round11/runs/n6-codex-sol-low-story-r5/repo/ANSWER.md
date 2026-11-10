# Offline Hedera transfer

Installed the current npm release of `@hiero-ledger/sdk` (2.91.0) and added `src/transfer.ts`. Run it with `npx tsx src/transfer.ts`. It loads `.env`, creates a 1 hbar transfer from `OPERATOR_ID` to `RECIPIENT_ID` with memo `invoice 42`, node `0.0.3`, and an operator transaction ID starting at `VALID_START` Unix seconds. It signs with the DER encoded ED25519 `OPERATOR_KEY` and writes only the signed transaction bytes as hex to stdout. It never creates a client or submits the transaction.

Verified `npx tsc --noEmit` passes. Ran the script with the supplied `.env` and decoded its output to confirm the transfer type, memo, operator, valid start, and signature. The decoded transaction has one signature.

The colleague's note applied to the package choice: `@hiero-ledger/sdk` is the current package, while `@hashgraph/sdk` remains at 2.81.0. Its API guidance for `PrivateKey.fromStringDer` and `TransactionId.withValidStart` also applied. There was no existing `@hashgraph/sdk` dependency to replace.
