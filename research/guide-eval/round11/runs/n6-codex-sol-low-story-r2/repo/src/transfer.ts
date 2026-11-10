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

const operator = AccountId.fromString(required("OPERATOR_ID"));
const recipient = AccountId.fromString(required("RECIPIENT_ID"));
const key = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const validStartText = required("VALID_START");
const validStart = Number(validStartText);
if (!/^\d+$/.test(validStartText) || !Number.isSafeInteger(validStart)) {
  throw new Error("VALID_START must be Unix seconds");
}

const transaction = new TransferTransaction()
  .addHbarTransfer(operator, new Hbar(-1))
  .addHbarTransfer(recipient, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operator, new Timestamp(validStart, 0)))
  .freezeWith(null);

await transaction.sign(key);
process.stdout.write(Buffer.from(transaction.toBytes()).toString("hex") + "\n");
