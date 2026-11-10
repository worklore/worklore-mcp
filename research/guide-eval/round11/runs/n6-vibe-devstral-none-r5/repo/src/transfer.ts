import { AccountId, PrivateKey, TransactionId, TransferTransaction, Hbar, Timestamp } from "@hashgraph/sdk";
import * as dotenv from "dotenv";

async function main() {
  dotenv.config();

  const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
  const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
  const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
  const validStartSeconds = parseInt(process.env.VALID_START!, 10);

  const transaction = new TransferTransaction()
    .setNodeAccountIds([AccountId.fromString("0.0.3")])
    .setTransactionId(
      TransactionId.withValidStart(operatorId, Timestamp.fromDate(validStartSeconds * 1000))
    )
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .setTransactionMemo("invoice 42");

  const frozenTx = await transaction.freeze();
  const signedTx = await frozenTx.sign(operatorKey);

  const bytes = await signedTx.toBytesAsync();
  console.log(Buffer.from(bytes).toString("hex"));
}

main();
