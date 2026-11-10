import { AccountId, Hbar, PrivateKey, Timestamp, TransactionId, TransferTransaction } from "@hashgraph/sdk";
import * as dotenv from "dotenv";

dotenv.config();

const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
const validStart = Timestamp.fromDate(new Date(Number(process.env.VALID_START) * 1000));

const tx: TransferTransaction = new TransferTransaction()
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .setTransactionMemo("invoice 42")
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1));

tx.freeze();
const signedTx = await tx.sign(operatorKey);

console.log(signedTx.toBytes().toString("hex"));
