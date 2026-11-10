# Answer

## What was done

1. **SDK dependency.** The current Hedera JavaScript SDK on npm is `@hiero-ledger/sdk`, version **2.91.0**. Installed with `npm install @hiero-ledger/sdk`. `@hashgraph/sdk` is not installed.
2. **`src/transfer.ts`** (run with `npx tsx src/transfer.ts`):
   - Reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 private key, hex), `RECIPIENT_ID`, and `VALID_START` (Unix seconds) from the environment. `.env` is loaded through `dotenv` (already a dependency) with `quiet: true`, so the dotenv banner does not pollute stdout.
   - Builds a `TransferTransaction`: -1 hbar from the operator, +1 hbar to the recipient, memo `invoice 42`, node `0.0.3`, transaction ID `OPERATOR_ID` with valid start `VALID_START` (nanos 0).
   - Freezes with `freezeWith(null)` (no `Client`), signs with the operator key, and prints only the signed transaction bytes as hex, followed by a newline.
   - Nothing is submitted. There is no `Client` or network call anywhere in the script.
3. **Typecheck.** `npx tsc --noEmit` passes with no errors.

## Result

With the `.env` test values, `npx tsx src/transfer.ts` exits 0 with empty stderr and prints one line of hex:

```
0ab1012aae010a440a0d0a0608c084fcd606120318e907120218031880c2d72f22020878320a696e766f696365203432721a0a180a0a0a0318e90710ff83af5f0a0a0a0318ea07108084af5f12660a640a2097e9921e6f6dc54c232342fcc19532353b87f8b5a02bede43a56da6bfb1a2a351a403aa49f428e2e0dafc462122b9930e788414382a4e0c7a3c339f6234eb097e8e9fee6a7e1cec38a9604b285f7adf107c8840b1ea0e8ee8d4edf91d03aec04a003
```

Repeated runs give identical output (Ed25519 signing is deterministic).

## How the output was verified

I checked the bytes offline with the SDK's own decoder (outside `src/`):

- Transaction ID: `0.0.1001@1793000000.000000000` (operator, valid start = `VALID_START`).
- Memo: `invoice 42`. Node: `0.0.3`.
- Transfers: `0.0.1001` -1 ℏ, `0.0.1002` +1 ℏ.
- One signature pair. Its public key prefix equals the operator's public key, and the Ed25519 signature verifies over the signed body bytes.

Verification used SDK internals (`_signedTransactions`) for the signature check only. The script itself uses only public API.

## Notes

- `package.json` now lists `@hiero-ledger/sdk` `^2.91.0`, and `package-lock.json` was created. Nothing is committed.
- `node_modules/` is untracked and there is no `.gitignore`. You may want to add one.
- Hbar amounts use `new Hbar(n)`. `Hbar.from(n)` does not compile in this SDK version because it requires a unit argument.

## Colleague's note: what applied

The note concerns the same SDK rename, so I checked each part against this project:

- **Applied: the package moved.** `npm view @hiero-ledger/sdk version` gives 2.91.0. `npm view @hashgraph/sdk version time.modified` gives 2.81.0, last modified 2026-03-13. So the current package is `@hiero-ledger/sdk`. I used it.
- **Applied: install and imports.** Installed `@hiero-ledger/sdk`. Imports (`AccountId`, `Hbar`, `PrivateKey`, `Timestamp`, `TransactionId`, `TransferTransaction`) come from `@hiero-ledger/sdk`. `PrivateKey.fromStringDer` and `TransactionId.withValidStart` work as the note described.
- **Applied: verification steps.** `npm ls @hiero-ledger/sdk` shows 2.91.0. `npm ls @hashgraph/sdk` shows nothing. `npx tsc --noEmit` passes. The output decodes to the expected transaction.
- **Not applicable: removing `@hashgraph/sdk`.** The project never had it, so there was nothing to replace.
- **Not applicable: `Client`-based setup and ground rules about deploy/publish.** The task forbids network submission, so the script builds offline. I did not deploy, publish, or submit anything.
- **Not used: the "Check if this applies" grep.** The project had no SDK dependency to begin with, so the grep only confirmed that.
- **Not used: the note's version timeline.** The npm `time.modified` data already confirmed the rename, so I did not rely on the note's specific dates or the claim that new releases come every few weeks.
