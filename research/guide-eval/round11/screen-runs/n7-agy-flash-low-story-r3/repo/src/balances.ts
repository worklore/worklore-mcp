import type { WalletBalanceRecord } from '@pollar/core';

/** One line per asset for the wallet screen, e.g. "USDC 12.50". */
export function balanceLines(records: WalletBalanceRecord[]): string[] {
  return records.map((r) => {
    const symbol = r.type === 'native' ? 'XLM' : r.code;
    const amount = r.balance === null ? '-' : parseFloat(r.balance).toFixed(2);
    return `${symbol} ${amount}`;
  });
}
