import type { WalletBalanceRecord } from '@pollar/core';

/** One line per asset for the wallet screen, e.g. "USDC 12.50". */
export function balanceLines(records: WalletBalanceRecord[]): string[] {
  return records.map((r) => `${r.type === 'native' ? 'XLM' : r.code} ${r.balance === null ? 'unavailable' : parseFloat(r.balance).toFixed(2)}`);
}
