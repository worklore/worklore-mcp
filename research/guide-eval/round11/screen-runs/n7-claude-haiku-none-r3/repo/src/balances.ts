import type { WalletBalanceRecord } from '@pollar/core';

/**
 * One line per asset for the wallet screen, e.g. "USDC 12.50". A null balance means the chain
 * could not be read, so it is shown as unavailable rather than as zero.
 */
export function balanceLines(records: WalletBalanceRecord[]): string[] {
  return records.map((r) => {
    const name = r.type === 'native' ? 'XLM' : r.code;
    return r.balance === null ? `${name} unavailable` : `${name} ${parseFloat(r.balance).toFixed(2)}`;
  });
}
