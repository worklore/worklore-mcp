import type { WalletBalanceRecord } from '@pollar/core';

/** One line per asset for the wallet screen, e.g. "USDC 12.50". */
export function balanceLines(records: WalletBalanceRecord[]): string[] {
  return records.map((r) => {
    const label = r.type === 'native' ? 'XLM' : r.code;
    // A null balance means the chain could not be read, not an empty wallet: never show it as 0.
    return `${label} ${r.balance === null ? 'unavailable' : parseFloat(r.balance).toFixed(2)}`;
  });
}
