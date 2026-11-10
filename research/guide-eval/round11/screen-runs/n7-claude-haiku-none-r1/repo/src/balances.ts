import type { WalletBalanceRecord } from '@pollar/core';

/**
 * One line per asset for the wallet screen, e.g. "USDC 12.50". A null balance means the chain could not
 * be read, so it shows as unavailable rather than 0.
 */
export function balanceLines(records: WalletBalanceRecord[]): string[] {
  const label = (r: WalletBalanceRecord) => (r.type === 'native' ? 'XLM' : r.code);
  return records.map((r) =>
    r.balance === null ? `${label(r)} unavailable` : `${label(r)} ${parseFloat(r.balance).toFixed(2)}`,
  );
}
