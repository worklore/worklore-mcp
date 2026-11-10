import dotenv from 'dotenv';
import {
  AccountId,
  PrivateKey,
  TransferTransaction,
  TransactionId,
  Hbar,
  Timestamp,
} from '@hiero-ledger/sdk';

dotenv.config();

const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
const validStart = parseInt(process.env.VALID_START!, 10);

const transaction = new TransferTransaction();
transaction.setTransactionId(
  TransactionId.withValidStart(operatorId, new Timestamp(validStart, 0))
);
transaction.addHbarTransfer(operatorId, new Hbar(-1));
transaction.addHbarTransfer(recipientId, new Hbar(1));
transaction.setTransactionMemo('invoice 42');
const nodeId = AccountId.fromString('0.0.3');
transaction.setNodeAccountIds([nodeId]);

const frozen = await transaction.freeze();
const signed = await frozen.sign(operatorKey);

process.stdout.write(signed.toBytes().toString('hex'));
