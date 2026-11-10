import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`missing environment variable ${name}`);
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
  const validStart = Timestamp.fromDate(Number(validStartRaw) * 1000);

  const nodeId = AccountId.fromString("0.0.3");

  const tx = new TransferTransaction()
    .addHbarTransfer(operatorId, Hbar.fromTinybars(-100_000_000))
    .addHbarTransfer(recipientId, Hbar.fromTinybars(100_000_000))
    .setTransactionMemo("invoice 42")
    .setNodeAccountIds([nodeId])
    .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
    .freeze();

  await tx.sign(operatorKey);

  process.stdout.write(Buffer.from(tx.toBytes()).toString("hex") + "\n");
}

main().catch((err: unknown) => {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
