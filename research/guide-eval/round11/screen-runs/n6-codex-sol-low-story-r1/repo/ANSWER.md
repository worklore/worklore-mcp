# Offline hbar transfer

Installed `@hiero-ledger/sdk` 2.91.0, the current npm version at the time of this change, and added `src/transfer.ts`. Run it with `npx tsx src/transfer.ts`. It reads the four values from `.env` or the environment, builds a 1 hbar transfer with memo `invoice 42`, node `0.0.3`, and the supplied transaction valid start, then signs it with the DER-encoded Ed25519 key. It writes only the signed transaction bytes as hexadecimal to stdout. It does not create a client or submit to a network.

Verified that `npx tsc --noEmit` passes and the command prints one hexadecimal line.

The colleague's package rename note applied: npm reports `@hiero-ledger/sdk` 2.91.0 and `@hashgraph/sdk` 2.81.0, so this project uses the Hiero package and its import. The replacement step did not apply because this project had no existing Hedera SDK dependency.
