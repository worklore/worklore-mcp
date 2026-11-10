import dotenv from 'dotenv';
import {
  TransferTransaction,
  PrivateKey,
  TransactionId,
  AccountId,
  Hbar,
  Timestamp,
} from '@hiero-ledger/sdk';

dotenv.config();

async function main() {
  const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
  const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
  const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
  const validStart = Timestamp.fromDate(
    new Date(Number(process.env.VALID_START!) * 1000)
  );

  const transaction = new TransferTransaction()
    .setNodeAccountIds([AccountId.fromString('0.0.3')])
    .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .setTransactionMemo('invoice 42');

  transaction.freeze();
  const signed = await transaction.sign(operatorKey);

  // The SDK has toBytes() at runtime but it's not in the type definitions
  // Cast to any to access it
  const bytes = (signed as any).toBytes();
  console.log(Buffer.from(bytes).toString('hex'));
}

main();
