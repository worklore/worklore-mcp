import { AccountId, Hbar, PrivateKey, Timestamp, TransactionId, TransferTransaction } from "@hiero-ledger/sdk";
import * as dotenv from "dotenv";

dotenv.config();

const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
const validStart = parseInt(process.env.VALID_START!, 10);

const transaction = new TransferTransaction()
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionId(
    TransactionId.withValidStart(
      operatorId,
      new Timestamp(validStart, 0)
    )
  )
  .setTransactionMemo("invoice 42");

transaction.freeze();
const signedTransaction = await transaction.signWith(
  operatorKey.publicKey,
  (message) => Promise.resolve(operatorKey.sign(message))
);

console.log(signedTransaction.toBytes().toString("hex"));
