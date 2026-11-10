import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";

const operatorIdStr = process.env.OPERATOR_ID;
const operatorKeyStr = process.env.OPERATOR_KEY;
const recipientIdStr = process.env.RECIPIENT_ID;
const validStartStr = process.env.VALID_START;

if (!operatorIdStr || !operatorKeyStr || !recipientIdStr || !validStartStr) {
  throw new Error("Missing required environment variables");
}

const operatorId = AccountId.fromString(operatorIdStr);
const operatorKey = PrivateKey.fromStringED25519(operatorKeyStr);
const recipientId = AccountId.fromString(recipientIdStr);
const validStartSeconds = Number(validStartStr);

const validStart = new Timestamp(validStartSeconds, 0);
const transactionId = new TransactionId(operatorId, validStart);
const nodeId = AccountId.fromString("0.0.3");

const transaction = new TransferTransaction()
  .setTransactionId(transactionId)
  .setNodeAccountIds([nodeId])
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .freeze();

const signedTransaction = await transaction.sign(operatorKey);
const transactionBytes = signedTransaction.toBytes();
const hexBytes = Buffer.from(transactionBytes).toString("hex");

console.log(hexBytes);
