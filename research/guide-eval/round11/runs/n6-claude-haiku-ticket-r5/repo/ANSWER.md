# Hedera transfer, built and signed offline

## What was done

1. **SDK installed:** `@hiero-ledger/sdk@^2.91.0` added to `dependencies` in `package.json` (`npm install @hiero-ledger/sdk`). The installed version is 2.91.0, the current `latest` on npm when checked.
2. **`src/transfer.ts` written.** It:
   - reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 private key, parsed with `PrivateKey.fromStringDer`), `RECIPIENT_ID` and `VALID_START` (Unix seconds) from the environment, loaded from `.env` with dotenv;
   - builds a `TransferTransaction` that moves 1 hbar from the operator to the recipient, memo `invoice 42`, node `0.0.3`, transaction ID `TransactionId.withValidStart(operatorId, Timestamp(VALID_START))`;
   - calls `freezeWith(null)` (no client, so no network access), signs with the operator key, and prints `toBytes()` as hex. That is the only output.
3. **Type check:** `npx tsc --noEmit` passes.

## Verification

Ran `npx tsx src/transfer.ts` with the `.env` test values. It exited 0 with empty stderr and printed a single hex string. Decoding that output with the protobuf definitions gave:

- memo: `invoice 42`
- transaction ID: `0.0.1001@1793000000.000000000`
- node: `0.0.3`
- transfers: `0.0.1001` −100000000 tinybar, `0.0.1002` +100000000 tinybar (1 hbar)
- one signature, from the operator public key, that verifies over the body bytes

Nothing was submitted to any network.

## Colleague's note: what applied

- **Applied:** the current SDK is `@hiero-ledger/sdk`. I checked npm: `@hiero-ledger/sdk` is at 2.91.0 (modified 2026-11-09), and `@hashgraph/sdk` is at 2.81.0 (modified 2026-03-13). I installed the new package directly.
- **Applied:** the APIs named in the note exist in 2.91.0 with the same names: `TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`. I used them as they are.
- **Did not apply:** the note's migration steps (removing `@hashgraph/sdk` and changing imports). `@hashgraph/sdk` was never installed in this project, so there was nothing to remove or rewrite.
- **Not checked:** the note's claim that the old package has no deprecation notice. The npm output I saw showed no `deprecated` field, which matches the note, but I did not confirm this beyond that.

## Notes

- `dotenv.config({ quiet: true })` is used because dotenv 17 otherwise writes a banner to stdout, which would break the "print only the bytes" requirement.
- `VALID_START` must be all digits; the script throws otherwise.
- The repo has no `.gitignore`, so `node_modules/` and `package-lock.json` show as untracked. I did not add one, since it wasn't requested.
