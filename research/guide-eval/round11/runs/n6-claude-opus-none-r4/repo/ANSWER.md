# What I did

## SDK package: `@hiero-ledger/sdk` 2.91.0 (not `@hashgraph/sdk`)

The Hedera JavaScript SDK is now published on npm as **`@hiero-ledger/sdk`**. It's built from the same
repository (`github.com/hiero-ledger/hiero-sdk-js`) that `@hashgraph/sdk` points to. The two names were
released side by side up to 2.81.0 (2026-03-13). After that, new releases went out only under
`@hiero-ledger/sdk`. Its `latest` tag on npm is 2.91.0, so `@hashgraph/sdk@2.81.0` is about ten minor
versions behind. The API is the same: only the import path changes.

Installed with `npm install --save-exact @hiero-ledger/sdk@2.91.0`.

Note: 2.91.0 was published on 2026-11-09, the same day I installed it, and it lists two more npm
maintainers than 2.90.0 does (both use hashgraph.com addresses). Because it's so new, I checked it before
using it:
- It was published from GitHub Actions with SLSA provenance, the same as 2.90.0.
- Its direct dependencies are the same as 2.90.0's, apart from patch or minor bumps of the
  `@hiero-ledger/proto` and `@hiero-ledger/cryptography` packages.
- The package has no install scripts.
- `npm audit signatures` passes (91 packages with verified signatures, 21 with attestations).

If you'd prefer to wait before adopting a release from the same day, pin `2.90.0` instead. It works the
same way for this script.

npm skipped two dependency postinstall scripts, as your npm config tells it to: `protobufjs` and
`esbuild`. Neither one is needed: tsx and the SDK both work without them.

## `src/transfer.ts`

- Loads `.env` with `dotenv/config` and reads `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID` and
  `VALID_START`. It stops with an error if any of them is missing, or if `VALID_START` isn't a whole
  number of seconds.
- Parses the key with `PrivateKey.fromStringDer`, which accepts DER-encoded hex.
- Builds a `TransferTransaction` that sends −1 ℏ from the operator and +1 ℏ to the recipient.
  - The memo is `invoice 42`, built from the existing `TREASURY_MEMO_PREFIX` in `src/index.ts`.
  - The node is set to `0.0.3`.
  - The transaction ID is `TransactionId.withValidStart(operator, Timestamp(VALID_START, 0))`.
- Calls `freeze()` without a `Client`. It's never connected to a network and nothing is sent.
- Signs with the operator key and prints only `toBytes()` as hex.

Default values the SDK filled in: max transaction fee 1 ℏ, valid duration 120 s. Ed25519 signatures are
deterministic, so the same inputs always give the same output.

## Checks

- `npx tsc --noEmit` passes.
- `npx tsx src/transfer.ts` prints one hex line. Two runs gave the same output.
- I decoded the output in a throwaway script, which I then deleted:
  - transaction ID `0.0.1001@1793000000.000000000`
  - memo `invoice 42`
  - node `[0.0.3]`
  - transfers `0.0.1001 −1 ℏ`, `0.0.1002 +1 ℏ`
  - the operator's public key verifies the signature

With the `.env` test values, the output is:

```
0ab1012aae010a440a0d0a0608c084fcd606120318e907120218031880c2d72f22020878320a696e766f696365203432721a0a180a0a0a0318e90710ff83af5f0a0a0a0318ea07108084af5f12660a640a2097e9921e6f6dc54c232342fcc19532353b87f8b5a02bede43a56da6bfb1a2a351a403aa49f428e2e0dafc462122b9930e788414382a4e0c7a3c339f6234eb097e8e9fee6a7e1cec38a9604b285f7adf107c8840b1ea0e8ee8d4edf91d03aec04a003
```

## Other changes

- `package.json` / `package-lock.json`: added the dependency.
- `.gitignore`: added so that `node_modules/` isn't committed.
- Nothing was committed or submitted.
