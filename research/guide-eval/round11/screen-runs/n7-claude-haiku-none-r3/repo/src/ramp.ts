import { isPollarApiError, type PollarClient, type RampQuote } from '@pollar/core';

/** Pesos per USDC for one quote: what the user pays in ARS divided by what they receive in USDC. */
function pesosPerUsdc(quote: RampQuote): number | null {
  const usdc = Number(quote.amountOut);
  return usdc > 0 ? Number(quote.amountIn) / usdc : null;
}

/**
 * "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes.
 * Pollar 0.12 quotes a route per fiat rail, so every ARS-to-USDC route is quoted and the cheapest rate wins.
 */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const matching = routes.filter((r) => r.fiat.country === 'AR' && r.fiat.currency === 'ARS' && r.asset.code === 'USDC');

  const results = await Promise.all(
    matching.map(async (route) => {
      try {
        const { quotes } = await client.quoteRamp({
          direction: 'ONRAMP',
          fiat: { currency: route.fiat.currency, rail: route.fiat.rail, country: route.fiat.country },
          asset: { code: route.asset.code, identifier: route.asset.identifier, chain: route.asset.chain },
          amount: { value: String(pesos), denomination: 'in' },
        });
        return quotes;
      } catch (err) {
        // A route with no quote is not an error for the user; it just does not count.
        if (isPollarApiError(err) && err.code === 'SDK_RAMPS_NO_ROUTE') return [];
        throw err;
      }
    }),
  );

  const rates = results.flat().map(pesosPerUsdc).filter((r): r is number => r !== null);
  return rates.length === 0 ? null : Math.min(...rates);
}
