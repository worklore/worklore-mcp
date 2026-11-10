# Answer: offline hbar transfer with the Hedera JavaScript SDK

## What was done

1. **Checked which SDK package is current.** `npm view` showed two packages:
   - `@hashgraph/sdk`: latest is `2.81.0`, last modified 2026-03-13. Its npm entry is still tagged `latest`.
   - `@hiero-ledger/sdk`: latest is `2.91.0`, modified today (2026-11-09).

   The current version is therefore in `@hiero-ledger/sdk`, not `@hashgraph/sdk`. `npm view <pkg> version` alone shows only a version number, so the modification dates were needed to see that `@hashgraph/sdk` had stopped.

2. **Installed `@hiero-ledger/sdk@^2.91.0`** (resolved to 2.91.0). `@hashgraph/sdk` is not installed. `package.json` lists only `@hiero-ledger/sdk`.

3. **Wrote `src/transfer.ts`**:
   - Reads `OPERATOR_ID`, `OPERATOR_KEY` (DER hex, parsed with `PrivateKey.fromStringDer`), `RECIPIENT_ID`, and `VALID_START` (Unix seconds) from the environment. `dotenv/config` loads `.env`, which is already a dependency.
   - Builds a `TransferTransaction`: -1 hbar from the operator, +1 hbar to the recipient, memo `invoice 42`.
   - Sets the transaction ID to `TransactionId.withValidStart(operator, new Timestamp(VALID_START, 0))` and the node to `0.0.3`.
   - Calls `freezeWith(null)` so no `Client` or network is used, then signs with the operator key and prints the bytes as hex.

## How to run

```
npx tsx src/transfer.ts
npx tsc --noEmit
```

`tsc --noEmit` passes with no errors. The script prints only the hex string on stdout.

## Verification (offline)

- Two runs with the same `.env` produced identical output, so the output is deterministic.
- The output decodes with `Transaction.fromBytes` to:
  - payer / transaction ID account: `0.0.1001`
  - valid start: `1793000000`
  - node: `0.0.3`
  - memo: `invoice 42`
  - transfers: `0.0.1001 -1 ℏ`, `0.0.1002 1 ℏ`
  - a 64-byte signature is present.
- Nothing was submitted to any network.

## Colleague's note: what applied

- **Applied:** the package was renamed. `@hashgraph/sdk` stopped at 2.81.0 on 2026-03-13 while `npm` still tags it `latest`, and `@hiero-ledger/sdk` is the current package. Comparing modification dates was the reliable check. I did not rely on the `latest` tag.
- **Applied:** the class names in the note (`TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`) all exist in 2.91.0 with the same usage. The only import change is the package name.
- **Did not apply exactly:** the note says the code "otherwise stayed the same". In 2.91.0, `Hbar.from` requires a unit argument. A call like `Hbar.from(1)` fails the type check, so the script uses `Hbar.from(1, HbarUnit.Hbar)`. The note's 2.81.0 code may not have needed this, but I did not test that version.
- **Not used:** the note's workflow of comparing against an earlier install. The repo had no earlier SDK installed.

## Choices I made

- `VALID_START` is passed directly as seconds with nanos 0, rather than through a `Date`.
- `freezeWith(null)` is used because the node and transaction ID are set explicitly, which avoids needing a network client.
- The script exits with an error if a required variable is missing or `VALID_START` is not a non-negative integer.
- The `.env` values are test values, so they are used as-is. The script prints no secrets.
