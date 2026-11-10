import dotenv from "dotenv";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";
import * as HieroProto from "@hiero-ledger/proto";

dotenv.config();

const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
const validStart = new Timestamp(Number(process.env.VALID_START!), 0);

const transaction = new TransferTransaction()
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .freeze();

transaction.sign(operatorKey);

// Access internal signed transaction and encode it
const signedTransaction = (transaction as any)._signedTransactions.get(0);
const signedBytes = (HieroProto as any).default.proto.SignedTransaction.encode(signedTransaction).finish();
console.log(signedBytes.toString("hex"));
