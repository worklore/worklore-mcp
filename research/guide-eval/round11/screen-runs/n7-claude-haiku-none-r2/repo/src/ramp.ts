import { isPollarApiError, type PollarClient } from '@pollar/core';

/**
 * "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes.
 * The rate is pesos per USDC (amountIn / amountOut), the lowest across every route and quote.
 */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const usdcRoutes = routes.filter(
    (r) => r.fiat.country === 'AR' && r.fiat.currency === 'ARS' && r.asset.code === 'USDC' && r.asset.chain === 'STELLAR',
  );
  const rates = await Promise.all(
    usdcRoutes.map(async (route) => {
      try {
        const res = await client.quoteRamp({
          direction: 'ONRAMP',
          fiat: route.fiat,
          asset: route.asset,
          amount: { value: String(pesos), denomination: 'in' },
        });
        return res.quotes.map((q) => Number(q.amountIn) / Number(q.amountOut));
      } catch (err) {
        // 0.12 throws SDK_RAMPS_NO_ROUTE (422) when a route has no quote; that just means no rate from this route.
        if (isPollarApiError(err) && err.code === 'SDK_RAMPS_NO_ROUTE') return [];
        throw err;
      }
    }),
  );
  const best = rates.flat().filter((rate) => Number.isFinite(rate) && rate > 0);
  return best.length > 0 ? Math.min(...best) : null;
}
