import { AccountId, Hbar, PrivateKey, Timestamp, TransactionId, TransferTransaction } from "@hiero-ledger/sdk";
import * as dotenv from "dotenv";
import Long from "long";

dotenv.config();

async function main() {
  const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
  const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
  const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
  const validStart = Long.fromNumber(parseInt(process.env.VALID_START!, 10));

  const txId = TransactionId.withValidStart(
    operatorId,
    new Timestamp(validStart, Long.ZERO)
  );

  const transfer = new TransferTransaction()
    .setTransactionId(txId)
    .setNodeAccountIds([AccountId.fromString("0.0.3")])
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .setTransactionMemo("invoice 42");

  const frozen = await transfer.freeze();
  const signed = await frozen.sign(operatorKey);
  const bytes = await signed.toBytesAsync();

  console.log(Buffer.from(bytes).toString("hex"));
}

main().catch(console.error);
