# What I did

## SDK package: `@hiero-ledger/sdk@2.91.0`
The Hedera JavaScript SDK now ships on npm as **`@hiero-ledger/sdk`**. The old
`@hashgraph/sdk` package is still there, but it stopped at 2.81.0 (March 2026), and its
README is now the "Hiero JavaScript SDK". Both packages come from the same repository
(`hiero-ledger/hiero-sdk-js`). The current release is `@hiero-ledger/sdk` **2.91.0**.

- I pinned it exactly (`"@hiero-ledger/sdk": "2.91.0"`) because this payload is signed
  and handed to another service.
- Note: 2.91.0 was published on 2026-11-09, the same day I installed it. It was
  published by GitHub Actions with SLSA provenance, the same way as 2.90.1, and
  `npm audit signatures` reports verified attestations. If you'd rather wait until a
  release has been out for a while, `2.90.1` has the same dependency set apart from
  patch bumps to `@hiero-ledger/proto` and `@hiero-ledger/cryptography`.
- npm did not run any install scripts (protobufjs, esbuild postinstall) because they
  aren't allow-listed. Everything works without them.

## `src/transfer.ts`
- Loads `.env` with dotenv using `quiet: true`. Without it, dotenv 17 prints a banner to
  stdout, which would corrupt the output.
- Reads `OPERATOR_ID`, `OPERATOR_KEY` (`PrivateKey.fromStringDer`, and rejects keys that
  aren't ED25519), `RECIPIENT_ID` and `VALID_START`. `VALID_START` must be whole seconds;
  nanos are set to 0.
- Builds a `TransferTransaction` that moves −1 ℏ from the operator and +1 ℏ to the
  recipient. The memo is `invoice 42`, built from the existing `TREASURY_MEMO_PREFIX` in
  `src/index.ts`. The node is `0.0.3`, and the transaction ID is
  `TransactionId.withValidStart(operator, VALID_START)`.
- Calls `freeze()` with no client, so it is fully offline and nothing touches the
  network. Then it signs with the operator key and writes only the hex of `toBytes()`
  to stdout.
- The max fee and valid duration are left at the SDK defaults (2 ℏ, 120 s).

## Checks
- `npx tsc --noEmit` passes.
- `npx tsx src/transfer.ts` prints one hex line. Running it again with the same inputs
  gives identical bytes (ED25519 signing is deterministic).
- I decoded the output with `Transaction.fromBytes` (throwaway script, now deleted). It
  is a TransferTransaction with memo `invoice 42`, ID `0.0.1001@1793000000.000000000`,
  node `[0.0.3]` and transfers `0.0.1001 −1 ℏ` / `0.0.1002 +1 ℏ`. The signature verifies
  against the operator's public key.
- I also added a `.gitignore` for `node_modules/`.
