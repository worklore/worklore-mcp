# Offline hbar transfer

Installed the current npm release of `@hiero-ledger/sdk` (2.91.0) and added `src/transfer.ts`. The script loads `.env`, builds a 1 hbar transfer from `OPERATOR_ID` to `RECIPIENT_ID`, sets memo `invoice 42`, node `0.0.3`, and a transaction ID using `VALID_START` as Unix seconds. It signs with the DER-encoded ED25519 `OPERATOR_KEY` and prints only the signed transaction bytes as hex. It creates no client and sends nothing to the network.

Run with `npx tsx src/transfer.ts`.

Verified with `npx tsc --noEmit` and a local run. Decoding the output confirmed the transaction type, memo, operator transaction ID, valid start, node, two hbar transfer entries, and a signature.

The colleague's note applied to the package choice: npm currently lists `@hiero-ledger/sdk` at 2.91.0, while `@hashgraph/sdk` remains at 2.81.0. The named SDK APIs also applied. This project had no old SDK dependency or imports to replace, so that migration step did not apply.
