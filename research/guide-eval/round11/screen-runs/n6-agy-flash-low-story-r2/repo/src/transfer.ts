import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

async function main(): Promise<void> {
  const operatorIdStr = process.env.OPERATOR_ID;
  const operatorKeyStr = process.env.OPERATOR_KEY;
  const recipientIdStr = process.env.RECIPIENT_ID;
  const validStartStr = process.env.VALID_START;

  if (!operatorIdStr || !operatorKeyStr || !recipientIdStr || !validStartStr) {
    throw new Error("Missing required environment variables in .env");
  }

  const operatorId = AccountId.fromString(operatorIdStr);
  const recipientId = AccountId.fromString(recipientIdStr);
  const operatorKey = PrivateKey.fromStringDer(operatorKeyStr);

  const validStartSec = Number(validStartStr);
  const validStart = new Timestamp(validStartSec, 0);
  const transactionId = TransactionId.withValidStart(operatorId, validStart);

  const transaction = new TransferTransaction()
    .setNodeAccountIds([AccountId.fromString("0.0.3")])
    .setTransactionId(transactionId)
    .setTransactionMemo("invoice 42")
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .freeze();

  const signedTransaction = await transaction.sign(operatorKey);
  const bytes = signedTransaction.toBytes();
  const hex = Buffer.from(bytes).toString("hex");

  console.log(hex);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
