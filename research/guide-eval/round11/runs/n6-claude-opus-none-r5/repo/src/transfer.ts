import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";
import { TREASURY_MEMO_PREFIX } from "./index.ts";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (value === undefined || value.trim() === "") {
    throw new Error(`Missing required environment variable ${name}`);
  }
  return value.trim();
}

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

const validStartRaw = requireEnv("VALID_START");
if (!/^\d+$/.test(validStartRaw)) {
  throw new Error(`VALID_START must be a non-negative integer (Unix seconds), got "${validStartRaw}"`);
}
const validStart = new Timestamp(Number(validStartRaw), 0);

const amount = new Hbar(1);

const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, amount.negated())
  .addHbarTransfer(recipientId, amount)
  .setTransactionMemo(`${TREASURY_MEMO_PREFIX} 42`)
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .freeze(); // no Client: node IDs and transaction ID are set explicitly, so this works offline

const signed = await transaction.sign(operatorKey);

process.stdout.write(Buffer.from(signed.toBytes()).toString("hex") + "\n");
