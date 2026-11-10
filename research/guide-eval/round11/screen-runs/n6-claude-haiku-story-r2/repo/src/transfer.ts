import { config } from "dotenv";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

// Load .env if present. Variables already set in the environment take precedence.
// `quiet` keeps dotenv's banner off stdout, which must carry only the transaction hex.
config({ quiet: true });

function required(name: string): string {
  const value = process.env[name];
  if (value === undefined || value.trim() === "") {
    throw new Error(`missing environment variable ${name}`);
  }
  return value.trim();
}

const NODE_ACCOUNT_ID = "0.0.3";
const ED25519_PKCS8_PREFIX = "302e020100300506032b657004220420";

async function main(): Promise<void> {
  const operatorId = AccountId.fromString(required("OPERATOR_ID"));
  const operatorKeyDer = required("OPERATOR_KEY");
  const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
  const validStartRaw = required("VALID_START");

  if (!/^\d+$/.test(validStartRaw)) {
    throw new Error("VALID_START must be a Unix time in whole seconds");
  }
  const validStartSeconds = Number(validStartRaw);
  if (!Number.isSafeInteger(validStartSeconds)) {
    throw new Error("VALID_START is out of range");
  }

  if (!operatorKeyDer.toLowerCase().startsWith(ED25519_PKCS8_PREFIX)) {
    throw new Error("OPERATOR_KEY must be a DER-encoded ED25519 private key");
  }
  const operatorKey = PrivateKey.fromStringDer(operatorKeyDer);

  const tx = new TransferTransaction()
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .setTransactionMemo("invoice 42")
    .setNodeAccountIds([AccountId.fromString(NODE_ACCOUNT_ID)])
    .setTransactionId(
      TransactionId.withValidStart(operatorId, new Timestamp(validStartSeconds, 0)),
    )
    // freeze() without a client does no network I/O: the transaction ID and node are already set.
    .freeze();

  // sign() is asynchronous and returns a Promise; the signature is only attached once it resolves.
  await tx.sign(operatorKey);

  process.stdout.write(Buffer.from(tx.toBytes()).toString("hex") + "\n");
}

main().catch((err: unknown) => {
  process.stderr.write(`error: ${err instanceof Error ? err.message : String(err)}\n`);
  process.exitCode = 1;
});
