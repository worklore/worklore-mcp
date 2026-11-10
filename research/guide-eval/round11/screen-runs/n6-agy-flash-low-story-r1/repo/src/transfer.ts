import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

const operatorIdStr = process.env.OPERATOR_ID;
const operatorKeyStr = process.env.OPERATOR_KEY;
const recipientIdStr = process.env.RECIPIENT_ID;
const validStartStr = process.env.VALID_START;

if (!operatorIdStr || !operatorKeyStr || !recipientIdStr || !validStartStr) {
  throw new Error("Missing required environment variables");
}

const operatorId = AccountId.fromString(operatorIdStr);
const operatorKey = PrivateKey.fromStringDer(operatorKeyStr);
const recipientId = AccountId.fromString(recipientIdStr);
const validStart = new Timestamp(Number(validStartStr), 0);

const txId = TransactionId.withValidStart(operatorId, validStart);
const nodeId = AccountId.fromString("0.0.3");

const tx = new TransferTransaction()
  .setTransactionId(txId)
  .setNodeAccountIds([nodeId])
  .setTransactionMemo("invoice 42")
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .freeze();

const signedTx = await tx.sign(operatorKey);
const txBytes = signedTx.toBytes();
const hex = Buffer.from(txBytes).toString("hex");

console.log(hex);
