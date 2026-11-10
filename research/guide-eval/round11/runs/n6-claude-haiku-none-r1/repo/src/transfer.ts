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

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));

const validStartSeconds = Number(required("VALID_START"));
if (!Number.isSafeInteger(validStartSeconds) || validStartSeconds < 0) {
  throw new Error("VALID_START must be a non-negative integer (Unix seconds)");
}

const nodeId = AccountId.fromString("0.0.3");

const tx = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([nodeId])
  .setTransactionId(
    TransactionId.withValidStart(
      operatorId,
      new Timestamp(validStartSeconds, 0),
    ),
  );

// Freezing without a client is fine here: node account and transaction ID
// are set explicitly, so nothing is fetched from the network.
tx.freezeWith(null);
await tx.sign(operatorKey);

const bytes = tx.toBytes();
process.stdout.write(Buffer.from(bytes).toString("hex") + "\n");
