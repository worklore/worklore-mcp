import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";
import { TREASURY_MEMO_PREFIX } from "./index.js";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing environment variable ${name}`);
  }
  return value;
}

async function main(): Promise<void> {
  const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
  const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
  const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

  const validStartRaw = requireEnv("VALID_START");
  if (!/^\d+$/.test(validStartRaw)) {
    throw new Error("VALID_START must be Unix seconds (integer)");
  }
  const validStart = Timestamp.fromDate(new Date(Number(validStartRaw) * 1000));

  const nodeId = AccountId.fromString("0.0.3");
  const oneHbar = new Hbar(1);

  const tx = new TransferTransaction()
    .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
    .setNodeAccountIds([nodeId])
    .setTransactionMemo(`${TREASURY_MEMO_PREFIX} 42`)
    .addHbarTransfer(operatorId, oneHbar.negated())
    .addHbarTransfer(recipientId, oneHbar)
    .freeze();

  await tx.sign(operatorKey);

  const bytes = await tx.toBytesAsync();
  console.log(Buffer.from(bytes).toString("hex"));
}

main().catch((err: unknown) => {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
