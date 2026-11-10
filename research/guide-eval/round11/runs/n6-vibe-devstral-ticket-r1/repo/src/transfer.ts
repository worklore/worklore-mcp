// @ts-nocheck
import { AccountId, Hbar, PrivateKey, Timestamp, TransactionId, TransferTransaction } from "@hiero-ledger/sdk";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
  const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
  const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
  const validStart = parseInt(process.env.VALID_START!);

  const transaction = new TransferTransaction()
    .setNodeAccountIds([AccountId.fromString("0.0.3")])
    .setTransactionId(
      TransactionId.withValidStart(
        operatorId,
        new Timestamp(validStart, 0)
      )
    )
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .setTransactionMemo("invoice 42");

  const frozen = transaction.freeze();
  const signedTransaction = await frozen.sign(operatorKey);

  process.stdout.write(signedTransaction.toBytes().toString("hex"));
}

main();
