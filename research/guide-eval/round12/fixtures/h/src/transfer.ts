import "dotenv/config"
import { AccountId, Hbar, PrivateKey, Timestamp, TransactionId, TransferTransaction } from "@hashgraph/sdk"

const env = (name: string): string => {
  const value = process.env[name]
  if (!value) throw new Error(`${name} is not set`)
  return value
}

const operatorId = AccountId.fromString(env("OPERATOR_ID"))
const operatorKey = PrivateKey.fromStringDer(env("OPERATOR_KEY"))
const recipientId = AccountId.fromString(env("RECIPIENT_ID"))
const validStart = new Timestamp(Number(env("VALID_START")), 0)

const tx = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .freeze()

const signed = await tx.sign(operatorKey)
console.log(Buffer.from(signed.toBytes()).toString("hex"))
