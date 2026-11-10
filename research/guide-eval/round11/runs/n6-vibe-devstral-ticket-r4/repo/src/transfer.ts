import dotenv from "dotenv";
import {
  TransferTransaction,
  PrivateKey,
  TransactionId,
  AccountId,
  Hbar,
  Timestamp,
} from "@hiero-ledger/sdk";

dotenv.config();

async function main() {
  const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
  const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
  const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
  const validStart = parseInt(process.env.VALID_START!, 10);

  const transaction = new TransferTransaction()
    .setNodeAccountIds([AccountId.fromString("0.0.3")])
    .setTransactionId(
      TransactionId.withValidStart(
        operatorId,
        new Timestamp(validStart, 0),
      ),
    )
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .setTransactionMemo("invoice 42");

  const frozenTransaction = transaction.freeze();
  const signedTransaction = await frozenTransaction.signWith(
    operatorKey.publicKey,
    (message) => Promise.resolve(operatorKey.sign(message)),
  );

  const bytes = signedTransaction.toBytes();
  console.log(Buffer.from(bytes).toString("hex"));
}

main();
