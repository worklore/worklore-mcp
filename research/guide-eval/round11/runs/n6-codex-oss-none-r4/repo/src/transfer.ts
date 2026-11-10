import {
    AccountId,
    Hbar,
    PrivateKey,
    TransactionId,
    Timestamp,
    TransferTransaction,
} from "@hashgraph/sdk";
import * as dotenv from "dotenv";

dotenv.config();

// Environment variables (all strings). Validation is minimal for brevity.
const OPERATOR_ID = process.env.OPERATOR_ID as string;
const OPERATOR_KEY_DER = process.env.OPERATOR_KEY as string; // DER‑encoded hex
const RECIPIENT_ID = process.env.RECIPIENT_ID as string;
const VALID_START = Number(process.env.VALID_START);

// Parse IDs and key
const operatorAccount = AccountId.fromString(OPERATOR_ID);
const recipientAccount = AccountId.fromString(RECIPIENT_ID);
const operatorKey = PrivateKey.fromStringDer(OPERATOR_KEY_DER);

// Build a custom TransactionId with the supplied valid start timestamp
const validStartTimestamp = new Timestamp(VALID_START, 0);
const customTxId = TransactionId.withValidStart(operatorAccount, validStartTimestamp);

// Construct the transfer transaction – 1 hbar from operator to recipient
const tx = new TransferTransaction()
    .addHbarTransfer(operatorAccount, new Hbar(-1))
    .addHbarTransfer(recipientAccount, new Hbar(1))
    .setTransactionId(customTxId)
    .setNodeAccountIds([new AccountId(0, 0, 3)])
    .setTransactionMemo("invoice 42");

// Freeze the transaction (no client needed because we set all required fields)
tx.freeze();

// Sign with the operator's private key
tx.sign(operatorKey);

// Output signed transaction bytes as a hex string
const signedBytes = tx.toBytes();
console.log(Buffer.from(signedBytes).toString("hex"));

