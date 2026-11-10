Added the Hedera JavaScript SDK (v2.81.0) and an offline transfer script.

**What changed**

- `package.json`: added `@hashgraph/sdk` dependency.
- `.env`: sample environment values for operator ID/key, recipient ID, and a valid‑start Unix timestamp.
- `src/transfer.ts`:
  - loads env vars with `dotenv`.
  - parses `AccountId` and DER‑encoded `PrivateKey` (`fromStringDer`).
  - creates a `TransactionId` using the provided valid‑start timestamp.
  - builds a `TransferTransaction` for 1 hbar, memo `invoice 42`, node `0.0.3`.
  - signs with the operator key and prints the signed bytes as hex.

The script runs via `npx tsx src/transfer.ts` and compiles with `npx tsc --noEmit`. No network calls are made; it works entirely offline.
