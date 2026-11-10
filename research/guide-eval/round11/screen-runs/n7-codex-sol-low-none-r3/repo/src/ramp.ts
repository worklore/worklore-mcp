import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const eligible = routes.filter((r) =>
    r.fiat.country === 'AR' && r.fiat.currency === 'ARS' &&
    r.asset.chain === 'STELLAR' && r.asset.code === USDC.code && r.asset.identifier === USDC.issuer,
  );
  const results = await Promise.allSettled(eligible.map((route) => client.quoteRamp({
    direction: 'ONRAMP',
    fiat: route.fiat,
    asset: route.asset,
    amount: { value: String(pesos), denomination: 'in' },
  })));
  const rates = results.flatMap((result) => result.status === 'fulfilled'
    ? result.value.quotes.map((quote) => pesos / Number(quote.amountOut)).filter((rate) => Number.isFinite(rate) && rate > 0)
    : []);
  return rates.length ? Math.min(...rates) : null;
}
