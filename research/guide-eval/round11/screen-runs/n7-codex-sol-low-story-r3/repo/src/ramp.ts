import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const route = routes.find(({ fiat, asset }) =>
    fiat.country === 'AR' && fiat.currency === 'ARS' &&
    asset.chain === 'STELLAR' && asset.code === USDC.code && asset.identifier === USDC.issuer
  );
  if (!route) return null;
  const res = await client.quoteRamp({
    direction: 'ONRAMP',
    fiat: { country: route.fiat.country, currency: route.fiat.currency, rail: route.fiat.rail },
    asset: { code: route.asset.code, identifier: route.asset.identifier, chain: route.asset.chain },
    amount: { value: String(pesos), denomination: 'in' },
  });
  const quote = res.quotes[0];
  if (!quote) return null;
  const amountOut = Number(quote.amountOut);
  return amountOut > 0 ? Number(quote.amountIn) / amountOut : null;
}
