Installed `@hashgraph/sdk` 2.81.0 from npm and added `src/transfer.ts`.

The script loads `.env`, constructs a 1 hbar transfer from `OPERATOR_ID` to `RECIPIENT_ID`, sets memo `invoice 42`, node `0.0.3`, and the operator transaction ID with `VALID_START` as Unix seconds. It freezes and signs the transaction with the DER-encoded ED25519 `OPERATOR_KEY`, then prints only the signed transaction bytes as hex. It does not create a network client or submit the transaction.

Verified with `npx tsc --noEmit` and `npx tsx src/transfer.ts`.
