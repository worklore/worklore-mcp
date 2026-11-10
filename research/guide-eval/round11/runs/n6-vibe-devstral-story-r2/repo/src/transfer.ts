import { config } from "dotenv";
config();

import {
  AccountId,
  PrivateKey,
  TransferTransaction,
  TransactionId,
  Hbar,
  Timestamp,
} from "@hiero-ledger/sdk";

const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
const validStart = process.env.VALID_START!;

const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(
    TransactionId.withValidStart(
      operatorId,
      new Timestamp(Number(validStart), 0),
    ),
  )
  .freeze();

const signedTransaction = await transaction.sign(operatorKey);

process.stdout.write(Buffer.from(signedTransaction.toBytes()).toString("hex"));
