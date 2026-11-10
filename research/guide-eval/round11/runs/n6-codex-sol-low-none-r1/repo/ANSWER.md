Installed the current npm release of `@hashgraph/sdk` (2.81.0) and added `src/transfer.ts`.

The script loads `.env`, builds a 1 hbar transfer with memo `invoice 42`, node `0.0.3`, and the supplied valid start, then signs it with the DER encoded Ed25519 operator key. It writes only the signed transaction bytes as hex and makes no network submission.

Run with `npx tsx src/transfer.ts`. Type checking: `npx tsc --noEmit`.
