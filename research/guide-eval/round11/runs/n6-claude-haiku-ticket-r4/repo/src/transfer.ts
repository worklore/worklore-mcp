import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

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

  const validStartSeconds = Number(requireEnv("VALID_START"));
  if (!Number.isInteger(validStartSeconds) || validStartSeconds < 0) {
    throw new Error("VALID_START must be a non-negative integer (Unix seconds)");
  }
  const validStart = new Timestamp(validStartSeconds, 0);

  const nodeAccountId = AccountId.fromString("0.0.3");
  const amount = new Hbar(1);

  const transaction = new TransferTransaction()
    .addHbarTransfer(operatorId, amount.negated())
    .addHbarTransfer(recipientId, amount)
    .setTransactionMemo("invoice 42")
    .setNodeAccountIds([nodeAccountId])
    .setTransactionId(TransactionId.withValidStart(operatorId, validStart));

  // freezeWith(null): no client, so nothing is contacted over the network.
  transaction.freezeWith(null);
  await transaction.sign(operatorKey);

  const bytes = await transaction.toBytesAsync();
  console.log(Buffer.from(bytes).toString("hex"));
}

main().catch((err: unknown) => {
  const message = err instanceof Error ? err.message : String(err);
  console.error(`error: ${message}`);
  process.exit(1);
});
