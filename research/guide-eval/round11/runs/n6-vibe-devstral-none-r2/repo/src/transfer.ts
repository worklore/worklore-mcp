import { Client, PrivateKey, AccountId, TransferTransaction, Hbar, TransactionId, Timestamp } from "@hashgraph/sdk";
import * as dotenv from "dotenv";

dotenv.config();

const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
const validStartSeconds = Number(process.env.VALID_START);

const client = Client.forName("testnet");
client.setOperator(operatorId, operatorKey);

const tx = new TransferTransaction()
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, Timestamp.fromDate(new Date(validStartSeconds * 1000))))
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42");

const signedTx = await tx.sign(operatorKey);

console.log(signedTx.toBytes().toString("hex"));
