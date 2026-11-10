import { Client, PrivateKey, AccountId, TransferTransaction, Hbar, TransactionId, Timestamp } from "@hashgraph/sdk";
import * as dotenv from "dotenv";

dotenv.config();

const OPERATOR_ID = process.env.OPERATOR_ID!;
const OPERATOR_KEY = process.env.OPERATOR_KEY!;
const RECIPIENT_ID = process.env.RECIPIENT_ID!;
const VALID_START = parseInt(process.env.VALID_START!, 10);

const operatorKey = PrivateKey.fromBytes(Buffer.from(OPERATOR_KEY, "hex"));
const operatorId = AccountId.fromString(OPERATOR_ID);
const recipientId = AccountId.fromString(RECIPIENT_ID);

const client = Client.forTestnet();
client.setOperator(operatorId, operatorKey);

const tx = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, new Timestamp(VALID_START, 0)));

const frozenTx = tx.freeze();
const signedTx = await frozenTx.sign(operatorKey);

console.log(signedTx.toBytes().toString("hex"));
