import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  try {
    const { routes } = await client.getRampRoutes('ONRAMP');
    const route = routes.find(
      (r) =>
        r.fiat.country === 'AR' &&
        r.fiat.currency === 'ARS' &&
        r.asset.chain === 'STELLAR' &&
        r.asset.code === 'USDC' &&
        (r.asset.identifier === null || r.asset.identifier === USDC.issuer),
    ) ?? routes.find((r) => r.fiat.country === 'AR' && r.fiat.currency === 'ARS');

    if (!route) return null;

    const res = await client.quoteRamp({
      direction: 'ONRAMP',
      fiat: { currency: route.fiat.currency, rail: route.fiat.rail, country: route.fiat.country },
      asset: { code: route.asset.code, identifier: route.asset.identifier, chain: route.asset.chain },
      amount: { value: pesos.toString(), denomination: 'in' },
    });

    const bestQuote = res.quotes[0];
    if (!bestQuote) return null;

    const amountIn = parseFloat(bestQuote.amountIn);
    const amountOut = parseFloat(bestQuote.amountOut);
    if (!amountIn || !amountOut) return null;

    return amountIn / amountOut;
  } catch {
    return null;
  }
}
