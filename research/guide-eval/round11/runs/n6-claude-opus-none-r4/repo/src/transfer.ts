import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";
import { TREASURY_MEMO_PREFIX } from "./index.ts";

function requireEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`Missing required environment variable ${name}`);
  return value;
}

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

const validStartRaw = requireEnv("VALID_START");
if (!/^\d+$/.test(validStartRaw)) {
  throw new Error(`VALID_START must be a Unix timestamp in whole seconds, got "${validStartRaw}"`);
}
const validStart = new Timestamp(Number(validStartRaw), 0);

const amount = new Hbar(1);

// No Client is used: node and transaction ID are set explicitly, so freezing
// and signing happen entirely offline.
const tx = new TransferTransaction()
  .addHbarTransfer(operatorId, amount.negated())
  .addHbarTransfer(recipientId, amount)
  .setTransactionMemo(`${TREASURY_MEMO_PREFIX} 42`)
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .freeze();

const signed = await tx.sign(operatorKey);

console.log(Buffer.from(signed.toBytes()).toString("hex"));
