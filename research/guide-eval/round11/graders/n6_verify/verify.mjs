// usage: node verify.mjs <hex> <operatorId> <recipientId> <validStart> <publicKeyDer>
import { Transaction, TransferTransaction, PublicKey } from "@hiero-ledger/sdk"
const [hex, op, rc, start, pub] = process.argv.slice(2)
const r = {}
try {
  const tx = Transaction.fromBytes(Buffer.from(hex.trim(), "hex"))
  r.is_transfer = tx instanceof TransferTransaction
  const t = {}
  for (const [k, v] of tx.hbarTransfers) t[k.toString()] = v.toTinybars().toString()
  r.transfers = t
  r.amounts_ok = Object.keys(t).length === 2 && t[op] === "-100000000" && t[rc] === "100000000"
  r.memo_ok = tx.transactionMemo === "invoice 42"
  r.node_ok = tx.nodeAccountIds?.length === 1 && tx.nodeAccountIds[0].toString() === "0.0.3"
  r.txid_ok = tx.transactionId?.accountId?.toString() === op && tx.transactionId?.validStart?.seconds?.toString() === start
  r.signature_ok = PublicKey.fromString(pub).verifyTransaction(tx)
} catch (e) { r.error = String(e).slice(0, 300) }
r.ok = !!(r.is_transfer && r.amounts_ok && r.memo_ok && r.node_ok && r.txid_ok && r.signature_ok)
console.log(JSON.stringify(r))
