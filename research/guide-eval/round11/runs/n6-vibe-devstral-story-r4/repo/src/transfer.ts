import dotenv from 'dotenv';
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from '@hiero-ledger/sdk';

dotenv.config();

async function main() {
  const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
  const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
  const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
  const validStart = Timestamp.fromDate(new Date(Number(process.env.VALID_START!) * 1000));

  const transaction = new TransferTransaction()
    .setNodeAccountIds([AccountId.fromString('0.0.3')])
    .setTransactionId(
      TransactionId.withValidStart(operatorId, validStart)
    )
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .setTransactionMemo('invoice 42')
    .freeze();

  const signedTransaction = await transaction.sign(operatorKey);

  console.log(signedTransaction.toBytes().toString('hex'));
}

main();
