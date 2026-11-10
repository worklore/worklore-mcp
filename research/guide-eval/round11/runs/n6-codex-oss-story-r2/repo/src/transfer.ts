/**
 * Offline Hedera HBAR transfer signing script.
 *
 * Reads the following environment variables (via a .env file if present):
 *   - OPERATOR_ID   : AccountId of the operator (e.g. "0.0.1234")
 *   - OPERATOR_KEY  : DER‑encoded hex string of the operator's ED25519 private key
 *   - RECIPIENT_ID  : AccountId of the transfer destination
 *   - VALID_START   : Unix timestamp (seconds) for the transaction ID's valid start
 *
 * Builds a TransferTransaction that moves 1 HBAR from the operator to the
 * recipient, uses node 0.0.3, sets memo "invoice 42", and forces the transaction
 * ID to use the supplied valid‑start timestamp. The transaction is frozen,
 * signed with the operator key, and the signed bytes are printed as a hex
 * string. No network request is performed.
 */

import { config } from "dotenv";
import {
    AccountId,
    PrivateKey,
    TransactionId,
    TransferTransaction,
    Hbar,
    Timestamp,
} from "@hiero-ledger/sdk";

// Load .env (if present) into process.env
config();

// Helper to abort with a clear message when a required variable is missing.
function requireEnv(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing required environment variable ${name}`);
    }
    return value;
}

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));
const validStartSec = Number(requireEnv("VALID_START"));
if (Number.isNaN(validStartSec) || validStartSec <= 0) {
    throw new Error("VALID_START must be a positive integer timestamp in seconds");
}
const validStart = Timestamp.fromDate(new Date(validStartSec * 1000));

// Build the transaction.
const tx = new TransferTransaction()
    .addHbarTransfer(operatorId, new Hbar(-1)) // debit operator
    .addHbarTransfer(recipientId, new Hbar(1)) // credit recipient
    .setTransactionMemo("invoice 42")
    .setNodeAccountIds([new AccountId(0, 0, 3)])
    .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
    .freeze();

// Sign with the operator's private key.
tx.sign(operatorKey);

// Output the signed transaction bytes as hex.
const bytes = tx.toBytes();
console.log(Buffer.from(bytes).toString("hex"));
