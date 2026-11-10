# Answer

## What was done

1. **Installed the SDK under its current name.** `npm install @hiero-ledger/sdk@latest`
   resolved to **2.91.0**. `@hashgraph/sdk` is not installed.
2. **Wrote `src/transfer.ts`.** It builds a 1 hbar transfer from `OPERATOR_ID` to
   `RECIPIENT_ID` with memo `invoice 42`, node `0.0.3`, and a transaction ID for the
   operator whose valid start is `VALID_START`. It signs with `OPERATOR_KEY` and prints
   the signed bytes as hex. Nothing is sent to a network: the node account and
   transaction ID are set explicitly and the transaction is frozen with `freezeWith(null)`,
   so no client is created.
3. **Checked the output** (see Verification below).

## Why `@hiero-ledger/sdk` and not `@hashgraph/sdk`

I checked the npm registry directly:

- `@hashgraph/sdk`: latest `2.81.0`, last modified 2026-03-13.
- `@hiero-ledger/sdk`: latest `2.91.0`, modified 2026-11-09, with releases through October and November.

`npm view @hashgraph/sdk version` alone looks current because it still reports `2.81.0`.
Comparing modification dates is what shows it is stale.

## Colleague's note: what applied

- **Applied:** use `@hiero-ledger/sdk`, not `@hashgraph/sdk`. Confirmed by the registry dates above.
- **Applied:** the imports and calls named in the note (`TransferTransaction`,
  `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`) exist
  in 2.91.0 and compile unchanged.
- **Applied:** verification steps. `npm ls @hiero-ledger/sdk` shows 2.91.0, `npm ls @hashgraph/sdk`
  shows nothing, and `npx tsc --noEmit` passes.
- **Not applicable:** step 3 (replacing an existing `@hashgraph/sdk`). The project never had it.
- **Not applicable:** the "Hedera docs" and "Has the problem" sections. They describe
  other projects' state; this one only needed the new name.
- **Ground rules:** applied. Work stayed in this directory and nothing was published or submitted.

## Verification

- `npx tsc --noEmit`: passes (exit 0).
- `npx tsx src/transfer.ts`: prints one line of hex and exits 0.
- Decoded the output with `Transaction.fromBytes`:
  - memo: `invoice 42`
  - transaction ID: `0.0.1001@1793000000.000000000`
  - node: `0.0.3`
  - transfers: `0.0.1001` −1 ℏ, `0.0.1002` +1 ℏ
- `PublicKey.verifyTransaction` with the operator key from `.env`: **true**.
  The same check with an unrelated generated key: **false**.
- Two runs produce identical bytes (deterministic output).

## Notes

- `.env` is tracked in git and contains `OPERATOR_KEY`. The values are test values, but
  the private key is in the repository. Consider moving secrets out of git before this
  is used with real keys.
- There is no `.gitignore`, so `node_modules/` shows as untracked. I did not add one.
- `package.json` now lists `@hiero-ledger/sdk` (`^2.91.0`) and `package-lock.json` was created.
- Nothing has been committed.
