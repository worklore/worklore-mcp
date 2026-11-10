# Hedera transfer, built and signed offline

## What was done

1. **SDK package.** I used `@hiero-ledger/sdk`, version `2.91.0`, which is the current `latest` on npm. I did not install `@hashgraph/sdk`.
   - `npm view @hashgraph/sdk` shows `latest: 2.81.0`, last modified 2026-03-13. `@hiero-ledger/sdk` was modified 2026-11-09 and is at 2.91.0.
   - The `dependencies` entry in `package.json` is `"@hiero-ledger/sdk": "^2.91.0"`. `npm install` was run, so `package-lock.json` exists.
2. **Script.** `src/transfer.ts` does the following:
   - Loads `.env` with `dotenv/config`, then reads `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID` and `VALID_START`. A missing variable, or a `VALID_START` that is not whole seconds, fails with a message on stderr.
   - Parses the key with `PrivateKey.fromStringDer`, and `VALID_START` as `new Timestamp(seconds, 0)`.
   - Builds a `TransferTransaction` with -1 hbar from the operator and +1 hbar to the recipient. The memo is `invoice 42`. The transaction ID is `TransactionId.withValidStart(operatorId, validStart)`. The node is `0.0.3`.
   - Calls `freezeWith(null)`, then `sign(operatorKey)`, then `toBytesAsync()`. It prints only the hex string to stdout.
   - Nothing is submitted. No client is created and no network call is made.
3. **Checks.**
   - `npx tsc --noEmit` exits 0.
   - `npx tsx src/transfer.ts` exits 0 with empty stderr and prints a 361-byte (722 hex characters) signed transaction.
   - I decoded that output with the SDK. Results: memo `invoice 42`, transaction ID `0.0.1001@1793000000.000000000`, node `0.0.3`, and transfers `0.0.1001 = -100000000` and `0.0.1002 = +100000000` tinybars. The single ED25519 signature verifies against the operator public key.
   - The scratch files I used for that decoding were deleted. Nothing else was written outside the project.

## Colleague's note: what applied

- **Applied: the package name.** The current SDK is `@hiero-ledger/sdk`. The old `@hashgraph/sdk` was frozen at 2.81.0 and still marked `latest`. I confirmed this from npm's modification dates and dist-tags.
- **Applied: the API calls.** I checked the 2.91.0 type declarations. `TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId` and `Hbar` all exist with the names and shapes the note describes. `HbarUnit` is also exported and is used here.
- **Did not apply: the migration step.** This project had no existing `@hashgraph/sdk` dependency or imports, so there was nothing to replace or remove.
- **Did not apply: the `npm view` check.** I did not run `npm view @hashgraph/sdk version` as the note did. I used `dist-tags` and the `time` field, which show the staleness more directly.
- **Differences from the note's version.** The note's code worked with `@hashgraph/sdk` 2.81.0. The current package's serialization method is `toBytesAsync()`, since `sign()` is async. The version used here relies on that.

## Notes

- `node_modules/` is not ignored by git, and the project has no `.gitignore`. I did not add one, since that was not requested.
- `npm install` printed install-script warnings for `protobufjs` and `esbuild`. These are dependency warnings, not errors, and the build and run both succeeded.
- `src/index.ts` is unchanged.
