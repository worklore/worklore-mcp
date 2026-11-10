Added `@hashgraph/sdk` 2.81.0 and `src/transfer.ts`. The script loads `.env`, creates a 1 hbar transfer with memo `invoice 42`, node `0.0.3`, and the specified operator transaction ID, then signs it locally with the DER encoded ED25519 key. It prints only the signed transaction bytes as hex and does not submit the transaction.

Run with `npx tsx src/transfer.ts`. Type check with `npx tsc --noEmit`.

Verified both commands locally. The output decodes to the requested transaction ID, node and memo, and contains one signature.
