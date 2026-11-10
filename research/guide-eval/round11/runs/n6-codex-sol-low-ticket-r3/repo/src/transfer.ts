import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const validStartText = required("VALID_START");
if (!/^\d+$/.test(validStartText) || !Number.isSafeInteger(Number(validStartText))) {
  throw new Error("VALID_START must be Unix seconds as a safe integer");
}

const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(
    TransactionId.withValidStart(operatorId, new Timestamp(Number(validStartText), 0)),
  )
  .freeze();

await transaction.sign(operatorKey);
process.stdout.write(Buffer.from(transaction.toBytes()).toString("hex") + "\n");
