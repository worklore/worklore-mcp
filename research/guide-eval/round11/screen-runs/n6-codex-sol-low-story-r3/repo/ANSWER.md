# Offline hbar transfer

Installed `@hiero-ledger/sdk` 2.91.0, the current npm release checked during this task. Added `src/transfer.ts`, which reads the four values from `.env` or the environment, builds a 1 hbar transfer from the operator to the recipient with memo `invoice 42`, node `0.0.3`, and an operator transaction ID starting at `VALID_START`. It freezes and signs the transaction with the DER-encoded ED25519 private key, then prints only the signed transaction bytes as lowercase hex. It creates no client and makes no network request.

Run with `npx tsx src/transfer.ts`. Verified that `npx tsc --noEmit` passes, the script emits one hex line, and the SDK can deserialize the output with the expected memo, node, transaction ID, and transfer entries.

The colleague's package-rename note applied: `@hiero-ledger/sdk` is current on npm, while `@hashgraph/sdk` remains at 2.81.0. Its suggested classes and methods also applied. Replacing an existing `@hashgraph/sdk` dependency did not apply because this project did not have one.
