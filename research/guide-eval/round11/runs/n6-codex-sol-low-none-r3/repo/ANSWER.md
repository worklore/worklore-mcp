Installed `@hashgraph/sdk` 2.81.0 from npm and added `src/transfer.ts`.

Run `npx tsx src/transfer.ts` to load the values from `.env`, build and sign the 1 hbar transfer with the specified memo, node, and transaction valid start, and print its serialized signed bytes as hex. The script does not create a client or submit the transaction.

Verified with `npx tsc --noEmit` and a local offline run of the script.
