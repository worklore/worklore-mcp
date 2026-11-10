import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const res = await client.quoteRamp({
    direction: 'ONRAMP',
    fiat: { currency: 'ARS', country: 'AR', rail: 'BANK_TRANSFER' },
    asset: { code: USDC.code, identifier: USDC.issuer, chain: 'STELLAR' },
    amount: { value: String(pesos), denomination: 'in' },
  });
  const best = res.quotes[0];
  if (!best) return null;
  return parseFloat(best.amountIn) / parseFloat(best.amountOut);
}
