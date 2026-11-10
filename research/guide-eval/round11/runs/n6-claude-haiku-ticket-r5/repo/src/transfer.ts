import { config } from "dotenv";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

// Load .env quietly: dotenv would otherwise log to stdout, and this script
// must print only the signed transaction bytes.
config({ quiet: true });

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`missing environment variable ${name}`);
  }
  return value;
}

const NODE_ACCOUNT_ID = "0.0.3";
const MEMO = "invoice 42";
const TRANSFER_AMOUNT = new Hbar(1);

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

const validStartRaw = requireEnv("VALID_START");
if (!/^\d+$/.test(validStartRaw)) {
  throw new Error(`VALID_START must be Unix seconds, got "${validStartRaw}"`);
}
const validStart = new Timestamp(Number(validStartRaw), 0);

const tx = new TransferTransaction()
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .setNodeAccountIds([AccountId.fromString(NODE_ACCOUNT_ID)])
  .setTransactionMemo(MEMO)
  .addHbarTransfer(operatorId, TRANSFER_AMOUNT.negated())
  .addHbarTransfer(recipientId, TRANSFER_AMOUNT);

// Offline: freeze without a client, so nothing is sent to a network.
tx.freezeWith(null);
await tx.sign(operatorKey);

console.log(Buffer.from(tx.toBytes()).toString("hex"));
