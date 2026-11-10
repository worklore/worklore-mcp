Installed `@hashgraph/sdk` 2.81.0, the current npm version, and added `src/transfer.ts`.

The script loads the four values from `.env`, creates a 1 hbar transfer from the operator to the recipient with memo `invoice 42`, node `0.0.3`, and a transaction ID starting at `VALID_START`. It freezes and signs the transaction locally with the DER-encoded ED25519 key, then prints only the signed bytes as hex. It does not connect to or submit to a network.

Verified with `npx tsc --noEmit` and `npx tsx src/transfer.ts`.
