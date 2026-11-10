import type { WalletBalanceRecord } from '@pollar/core';

/**
 * One line per asset for the wallet screen, e.g. "USDC 12.50".
 * A null balance means the chain could not be read, so it shows as unavailable rather than 0.
 */
export function balanceLines(records: WalletBalanceRecord[]): string[] {
  return records.map((r) => {
    const label = r.type === 'native' && (r.chain ?? 'STELLAR') === 'STELLAR' ? 'XLM' : r.code;
    return r.balance === null ? `${label} unavailable` : `${label} ${parseFloat(r.balance).toFixed(2)}`;
  });
}
