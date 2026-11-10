import type { PollarClient } from '@pollar/core';

/** "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const res = await client.getRampsQuote({ country: 'AR', currency: 'ARS', amount: pesos, direction: 'onramp' });
  return res.quotes[0]?.rate ?? null;
}
