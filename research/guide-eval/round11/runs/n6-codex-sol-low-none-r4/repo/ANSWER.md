Installed the current npm release of `@hashgraph/sdk` (2.81.0) and added `src/transfer.ts`.

Run `npx tsx src/transfer.ts` to load the values from `.env`, construct a 1 hbar transfer with the specified memo, node, and transaction valid start, sign it locally, and print only the signed transaction bytes as hex. The script does not create a client or submit the transaction.

Verified with `npx tsc --noEmit` and `npx tsx src/transfer.ts`.
