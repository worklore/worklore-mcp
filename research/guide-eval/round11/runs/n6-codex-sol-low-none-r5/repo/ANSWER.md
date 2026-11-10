# Offline HBAR transfer

Installed `@hashgraph/sdk` 2.81.0 from npm and added `src/transfer.ts`.
Run `npx tsx src/transfer.ts` with the supplied `.env` to print one line of
hex-encoded, signed transaction bytes. The script builds a 1 HBAR transfer
from `OPERATOR_ID` to `RECIPIENT_ID`, sets memo `invoice 42`, node `0.0.3`,
and an operator transaction ID starting at `VALID_START` Unix seconds. It
freezes and signs locally; it does not submit the transaction.

Verified with `npx tsc --noEmit`, executed the script, and decoded its output
with the SDK to confirm the transaction ID, node, memo, and transfer amounts.
