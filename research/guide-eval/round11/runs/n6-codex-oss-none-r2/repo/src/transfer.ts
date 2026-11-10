import { config } from 'dotenv';
import { AccountId, PrivateKey, TransactionId, Hbar, TransferTransaction, Timestamp } from '@hashgraph/sdk';

config(); // load .env

const operatorIdStr = process.env.OPERATOR_ID;
const operatorKeyDer = process.env.OPERATOR_KEY;
const recipientIdStr = process.env.RECIPIENT_ID;
const validStartStr = process.env.VALID_START;

if (!operatorIdStr || !operatorKeyDer || !recipientIdStr || !validStartStr) {
    throw new Error('Missing required environment variables');
}

const operatorId = AccountId.fromString(operatorIdStr);
const operatorKey = PrivateKey.fromStringDer(operatorKeyDer);
const recipientId = AccountId.fromString(recipientIdStr);
const validStart = Number(validStartStr);

// Create Timestamp for valid start (seconds, nanos)
const validTimestamp = new Timestamp(validStart, 0);
const transactionId = TransactionId.withValidStart(operatorId, validTimestamp);

const tx = new TransferTransaction()
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .setTransactionMemo('invoice 42')
    .setNodeAccountIds([AccountId.fromString('0.0.3')])
    .setTransactionId(transactionId)
    .freeze();

await tx.sign(operatorKey);

const signedBytes = tx.toBytes();
console.log(Buffer.from(signedBytes).toString('hex'));
