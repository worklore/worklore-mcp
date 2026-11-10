import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const res = await client.quoteRamp({
    direction: 'ONRAMP',
    fiat: { country: 'AR', currency: 'ARS', rail: 'BANK_TRANSFER' },
    asset: { code: USDC.code, identifier: USDC.issuer, chain: 'STELLAR' },
    amount: { value: String(pesos), denomination: 'in' },
  });
  const best = res.quotes[0];
  if (!best) return null;
  const inVal = parseFloat(best.amountIn);
  const outVal = parseFloat(best.amountOut);
  if (!outVal || isNaN(inVal) || isNaN(outVal)) return null;
  return inVal / outVal;
}
