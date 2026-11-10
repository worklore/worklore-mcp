import { Client, PrivateKey, AccountId, TransferTransaction, Hbar, Timestamp, TransactionId } from "@hashgraph/sdk";
import * as dotenv from "dotenv";

dotenv.config();

const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
const operatorKey = PrivateKey.fromStringED25519(process.env.OPERATOR_KEY!);
const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
const validStart = Timestamp.fromDate(Number(process.env.VALID_START!) * 1000);

const client = Client.forTestnet();
client.setOperator(operatorId, operatorKey);

const txId = new TransactionId(operatorId, validStart, false, 0);

const tx = new TransferTransaction()
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(txId)
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42");

const signedTx = await tx.signWithOperator(client);

console.log(signedTx.toBytes().toString("hex"));
