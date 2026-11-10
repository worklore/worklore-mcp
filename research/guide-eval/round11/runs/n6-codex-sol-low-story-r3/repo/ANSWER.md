# Offline hbar transfer

Installed the current npm release of `@hiero-ledger/sdk` (2.91.0) and added `src/transfer.ts`. Run it with `npx tsx src/transfer.ts`. It loads `.env`, constructs a 1 hbar transfer from `OPERATOR_ID` to `RECIPIENT_ID`, sets memo `invoice 42`, node `0.0.3`, and the operator transaction ID at `VALID_START` Unix seconds. It freezes without a client, signs with the DER-encoded ED25519 `OPERATOR_KEY`, and writes only the signed transaction bytes as hex to stdout. It makes no network submission.

Verified with `npx tsc --noEmit` and a local run. Decoding the output with the SDK confirmed the memo, node, transaction ID, and balanced hbar transfers; stdout contained only hex.

The colleague's package rename note applied: `@hiero-ledger/sdk` is the current package, while `@hashgraph/sdk` remains at 2.81.0. Its suggested SDK classes and offline transaction construction also applied. The note's 2.90.x version was superseded by npm's current 2.91.0 release. There was no old SDK dependency to remove.
