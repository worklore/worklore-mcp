import type { PollarClient } from '@pollar/core';

/** "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const res = await client.quoteRamp({
    direction: 'ONRAMP',
    fiat: { currency: 'ARS', rail: 'BANK_TRANSFER', country: 'AR' },
    asset: { code: 'USDC', identifier: null, chain: 'STELLAR' },
    amount: { value: pesos.toString(), denomination: 'in' },
  });
  const bestQuote = res.quotes[0];
  if (!bestQuote) return null;
  const amountIn = parseFloat(bestQuote.amountIn);
  const amountOut = parseFloat(bestQuote.amountOut);
  if (!amountIn || !amountOut) return null;
  return amountIn / amountOut;
}
