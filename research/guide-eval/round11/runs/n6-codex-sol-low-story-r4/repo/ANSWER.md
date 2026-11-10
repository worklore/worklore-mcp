# Offline hbar transfer

Installed `@hiero-ledger/sdk` 2.91.0 from npm and added `src/transfer.ts`. Run it with `npx tsx src/transfer.ts`. It reads the four required values from `.env` or the environment, builds the 1 hbar transfer with the requested memo, node, and valid start, signs it with the DER-encoded ED25519 key, and writes only the signed transaction bytes as hex. It does not create a client or submit the transaction.

Verification: `npx tsc --noEmit` passed. The script ran with the test `.env`; decoding its output showed the expected memo, node 0.0.3, operator transaction ID with the supplied valid start, and balanced -1/+1 hbar transfers.

The colleague's note applied to the package choice: `@hiero-ledger/sdk` is current on npm (2.91.0), while `@hashgraph/sdk` reports 2.81.0. The migration and removal steps did not apply because this project had no SDK dependency or imports before this change.
