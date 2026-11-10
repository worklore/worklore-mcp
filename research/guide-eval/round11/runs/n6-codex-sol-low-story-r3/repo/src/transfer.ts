import { config } from "dotenv";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

config({ quiet: true });

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

const operator = AccountId.fromString(required("OPERATOR_ID"));
const recipient = AccountId.fromString(required("RECIPIENT_ID"));
const key = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const validStart = Number(required("VALID_START"));
if (!Number.isSafeInteger(validStart) || validStart < 0) {
  throw new Error("VALID_START must be a nonnegative Unix timestamp in seconds");
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
