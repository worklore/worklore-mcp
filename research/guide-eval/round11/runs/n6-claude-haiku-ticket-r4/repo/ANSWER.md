# Answer: offline hbar transfer in TypeScript

## What was done

1. **SDK added: `@hiero-ledger/sdk` ^2.91.0.** This is the current Hedera JavaScript SDK on npm, published 2026-11-09. `npm view` shows `2.91.0` as the latest version. I did not use `@hashgraph/sdk`, the old name. Its last release is 2.81.0 and its README and npm metadata show no sign that the SDK moved to `@hiero-ledger`. I confirmed this from the npm registry's publish dates for the new package (2.89.1 on 2026-09-28, 2.90.0 on 2026-10-14, 2.91.0 on 2026-11-09). This is the caveat the colleague's note describes, and it applied: `npm view @hashgraph/sdk version` alone returns `2.81.0` and looks current.
2. **`src/transfer.ts` written.** Run it with `npx tsx src/transfer.ts`. It:
   - reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 private key, parsed with `PrivateKey.fromStringDer`), `RECIPIENT_ID` and `VALID_START` (Unix seconds) from the environment. `dotenv/config` loads `.env`. The script fails with a clear message if a variable is missing or `VALID_START` is not a non-negative integer;
   - builds a `TransferTransaction` that moves -1 hbar from the operator and +1 hbar to the recipient, with memo `invoice 42`;
   - sets node account `0.0.3`;
   - sets the transaction ID to `TransactionId.withValidStart(operatorId, new Timestamp(VALID_START, 0))`;
   - calls `freezeWith(null)`, which needs no client and makes no network call, then signs with the operator key;
   - prints only the signed transaction bytes as one line of hex to stdout. Errors go to stderr with exit code 1.
3. **`.gitignore` added** with `node_modules/`. Nothing in the repo ignored it before, so `npm install` would have left it untracked and easy to commit by accident.
4. **`package.json` / `package-lock.json`**: `@hiero-ledger/sdk` added to `dependencies`. `dotenv` was already a dependency, and I used it for `.env` loading.

## Verification

- `npx tsc --noEmit`: exits 0 with no errors.
- `npx tsx src/transfer.ts`: exits 0, writes one hex line to stdout and nothing to stderr. It made no network calls; the script never calls `execute` or `submit`.
- Decoding the output with the SDK:
  - memo: `invoice 42`;
  - transaction ID: `0.0.1001@1793000000.000000000`;
  - node: `0.0.3`;
  - transfers: `0.0.1001 = -100000000` tinybars and `0.0.1002 = +100000000` tinybars (1 hbar each way, sums to zero);
  - one signature, from a key matching the operator's public key, and it verifies as a 64-byte ED25519 signature over the body bytes.

## Colleague's note: what applied

- **Applied:** the package is `@hiero-ledger/sdk`, not `@hashgraph/sdk`. The new name is at 2.91.0 and the old one stopped at 2.81.0. I checked the publish dates myself rather than trusting the note.
- **Applied:** the class and method names in the note (`TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`) exist in 2.91.0 and I used them. The note's "one-line import change" was not a complete description. In 2.91.0, `Hbar.from(amount)` needs a unit argument, so I used `new Hbar(1)`, which defaults to hbar. I checked the typings for this rather than assuming the call was unchanged.
- **Not applied / not verified:** the note says the old package was "the wrong package" and that the switch needed only an import change. I did not test the old package in this project, so I can't confirm its exact behaviour beyond the publish dates and the repo metadata. The note's claim that `@hashgraph/sdk` has no deprecation notice is only what the colleague saw. I checked `npm view @hashgraph/sdk deprecated` and got no output, which agrees with that.

## Notes

- `.env` is tracked by git and contains `OPERATOR_KEY`. The values are described as test values, so I left it alone. If the key is ever real, it should be removed from the repo and rotated.
- The `npm install` output warned that `protobufjs` and `esbuild` have install scripts that are not yet approved. I did not change that setting.
- `VALID_START` is used only for the transaction ID. The network checks the transaction's validity window when it is submitted, which this script never does.
