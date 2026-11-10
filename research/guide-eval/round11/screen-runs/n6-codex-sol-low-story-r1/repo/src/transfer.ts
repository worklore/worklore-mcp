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
  if (!value) throw new Error(`${name} is required`);
  return value;
}

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const validStartText = required("VALID_START");
const validStart = Number(validStartText);
if (!/^\d+$/.test(validStartText) || !Number.isSafeInteger(validStart)) {
  throw new Error("VALID_START must be Unix seconds");
}

const amount = new Hbar(1);
const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, amount.negated())
  .addHbarTransfer(recipientId, amount)
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, new Timestamp(validStart, 0)))
  .freeze();

await transaction.sign(operatorKey);
process.stdout.write(Buffer.from(await transaction.toBytesAsync()).toString("hex") + "\n");
