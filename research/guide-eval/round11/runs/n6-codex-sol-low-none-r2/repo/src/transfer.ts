import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required`);
  return value;
}

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
const privateKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const validStart = required("VALID_START");
if (!/^\d+$/.test(validStart)) {
  throw new Error("VALID_START must be Unix seconds");
}

const transactionId = TransactionId.fromString(
  `${operatorId.toString()}@${validStart}.000000000`,
);
const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(transactionId)
  .freeze();

await transaction.sign(privateKey);
process.stdout.write(Buffer.from(await transaction.toBytesAsync()).toString("hex") + "\n");
