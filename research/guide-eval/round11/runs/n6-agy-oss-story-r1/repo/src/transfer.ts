import { config } from "dotenv";
import {
    AccountId,
    PrivateKey,
    TransactionId,
    TransferTransaction,
    Hbar,
} from "@hiero-ledger/sdk";

config();

const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
const validStartSec = Number(process.env.VALID_START!);

// Create TransactionId with the specific valid start
const validStart = new Date(validStartSec * 1000);
let txId = TransactionId.generate(operatorId);
if (typeof (txId as any).setValidStart === "function") {
    (txId as any).setValidStart(validStart);
} else if (typeof (txId as any).withValidStart === "function") {
    txId = (txId as any).withValidStart(validStart);
}

const tx = new TransferTransaction()
    .setTransactionId(txId)
    .addHbarTransfer(operatorId, Hbar.fromTinybars(-100_000_000)) // -1 HBAR
    .addHbarTransfer(recipientId, Hbar.fromTinybars(100_000_000))   // +1 HBAR
    .setTransactionMemo("invoice 42")
    .setNodeAccountIds([new AccountId(0, 0, 3)])
    .freeze();

tx.sign(operatorKey);

const signedBytes = tx.toBytes();
console.log(Buffer.from(signedBytes).toString("hex"));
