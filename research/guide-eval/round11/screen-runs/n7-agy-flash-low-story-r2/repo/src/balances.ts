import type { WalletBalanceRecord } from '@pollar/core';

/** One line per asset for the wallet screen, e.g. "USDC 12.50" or "USDC unavailable". */
export function balanceLines(records: WalletBalanceRecord[]): string[] {
  return records.map((r) => {
    const asset = r.type === 'native' ? 'XLM' : r.code;
    const balance = r.balance !== null ? parseFloat(r.balance).toFixed(2) : 'unavailable';
    return `${asset} ${balance}`;
  });
}
