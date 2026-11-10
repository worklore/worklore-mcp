import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing environment variable ${name}`);
  }
  return value;
}

async function main(): Promise<void> {
  const operatorId = AccountId.fromString(required("OPERATOR_ID"));
  const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
  const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
  const validStartSeconds = Number(required("VALID_START"));
  if (!Number.isInteger(validStartSeconds) || validStartSeconds < 0) {
    throw new Error("VALID_START must be a non-negative integer (Unix seconds)");
  }

  const nodeId = AccountId.fromString("0.0.3");
  const validStart = new Timestamp(validStartSeconds, 0);

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
