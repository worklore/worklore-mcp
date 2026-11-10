# What I did

## 1. Added the Hedera JavaScript SDK
- Checked npm: the current `latest` version of `@hashgraph/sdk` is **2.81.0** (dist-tags: `latest: 2.81.0`, `beta: 2.81.0-beta.1`).
- Ran `npm install @hashgraph/sdk@2.81.0`. This added `"@hashgraph/sdk": "^2.81.0"` to `dependencies` in `package.json` and created `package-lock.json`.
- npm held back the install scripts for `protobufjs` and `esbuild` (npm's install-script approval feature). I didn't approve them. `tsx`, `tsc` and the SDK all work without them.
- Added a `.gitignore` containing `node_modules/`.

## 2. Wrote `src/transfer.ts`
Run it with `npx tsx src/transfer.ts` (or `npm run transfer`).

- Loads `.env` with `dotenv` (`quiet: true`, so dotenv can't print a log line to stdout). Then it reads `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID` and `VALID_START`, and exits with an error if any is missing. `VALID_START` must be a whole number of Unix seconds.
- Parses the key with `PrivateKey.fromStringED25519`, which accepts the DER-encoded hex.
- Builds a `TransferTransaction`:
  - −1 hbar from the operator, +1 hbar to the recipient
  - transaction memo `invoice 42`
  - node account IDs `[0.0.3]`
  - transaction ID `TransactionId.withValidStart(operator, new Timestamp(VALID_START, 0))`
- Calls `.freeze()` with no client. It never creates a `Client` and never connects to a network, so it runs fully offline.
- Signs with the operator key and writes only `toBytes()` as hex, followed by a newline, to stdout.

The max transaction fee and the valid duration were not specified, so they keep the SDK defaults: 2 hbar max fee, 120 s valid duration.

## 3. Checks
- `npx tsc --noEmit` passes.
- `npx tsx src/transfer.ts` prints one line of hex and nothing else. Two runs give byte-identical output, because ED25519 signatures are deterministic.
- I decoded the output with `Transaction.fromBytes` in a temporary script, which I then deleted:
  - transaction ID `0.0.1001@1793000000.000000000`
  - memo `invoice 42`
  - node `0.0.3`
  - transfers `0.0.1001: -100000000` and `0.0.1002: +100000000` tinybar
  - `publicKey.verifyTransaction(tx)` returns `true`

Nothing was submitted to any network.
