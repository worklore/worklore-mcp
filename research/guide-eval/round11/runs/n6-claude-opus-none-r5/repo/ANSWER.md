# What I did

## Dependency
- Checked npm: `@hashgraph/sdk` `latest` is **2.81.0** (2026-11-09).
- `npm install @hashgraph/sdk@2.81.0` → `package.json` now has `"@hashgraph/sdk": "^2.81.0"`, and `package-lock.json` was created.
- npm skipped the install scripts for protobufjs and esbuild (npm's default policy for new packages). Building, signing and `tsx` all work without them, so I left them unapproved.
- Added `.gitignore` containing `node_modules/`.

## `src/transfer.ts`
Run with `npx tsx src/transfer.ts` (or `npm run transfer`).
- Loads `.env` with `dotenv/config` and reads `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID`, `VALID_START`. It fails with a clear error if any is missing or if `VALID_START` is not an integer.
- The key is parsed with `PrivateKey.fromStringDer` (DER-encoded hex ED25519).
- Builds a `TransferTransaction`: −1 ℏ from the operator, +1 ℏ to the recipient. The memo is `invoice 42`, built from the existing `TREASURY_MEMO_PREFIX` in `src/index.ts`. The node is `0.0.3`, and the transaction ID is `TransactionId.withValidStart(operator, new Timestamp(VALID_START, 0))`.
- Calls `freeze()` **without a `Client`**. This is possible because the node account IDs and transaction ID are set explicitly, so nothing touches the network. It then signs with the operator key.
- Prints only `toBytes()` as hex, followed by one newline.

## Verification
- `npx tsc --noEmit` passes.
- `npx tsx src/transfer.ts` prints one hex line. With the test `.env` it starts with `0ac9012ac601…`.
- I decoded that output with `Transaction.fromBytes` in a throwaway script, since deleted. It shows transaction ID `0.0.1001@1793000000.000000000`, memo `invoice 42`, node `[0.0.3]`, and transfers `0.0.1001: -1 ℏ` and `0.0.1002: 1 ℏ`. `publicKey.verifyTransaction` returns `true`.
- Ed25519 signatures are deterministic, so the output is the same on every run for the same inputs.
- Nothing was submitted to any network.

## Notes
- The SDK's default transaction fee (2 ℏ max) and valid duration (120 s) are used. The submitting service must send the transaction within 120 s of `VALID_START`, or the network will reject it.
- `.env` is tracked in git and holds a private key. That's fine for test values, but don't commit real ones.
