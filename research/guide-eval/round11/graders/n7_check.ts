// Hidden runtime checks, run with `npx tsx check.ts` from inside the agent's project.
// Imports the agent's modules and drives them with fake Pollar clients: no network.
const out: Record<string, unknown> = {};
const run = async (name: string, f: () => Promise<unknown>) => {
  try { out[name] = await f(); } catch (e) { out[name] = { error: String((e as Error)?.message ?? e).slice(0, 300) }; }
};
const mod = (p: string) => import(new URL(p, `file://${process.cwd()}/`).href);

await run('base_url', async () => {
  const { pollarConfig } = await mod('./src/pollar.ts');
  const u = pollarConfig?.baseUrl ?? pollarConfig?.client?.baseUrl;
  return { value: u ?? null, ok: u == null || /^https:\/\/sdk\.api\.pollar\.xyz\/?$/.test(u) };
});

await run('balances', async () => {
  const { balanceLines } = await mod('./src/balances.ts');
  const base = { available: null, enabledInApp: true, trustlineRemoved: false, chain: 'STELLAR', decimals: 7 };
  const lines: string[] = balanceLines([
    { ...base, type: 'credit_alphanum4', code: 'USDC', issuer: 'G', balance: null },
    { ...base, type: 'native', code: 'XLM', balance: '12.5', available: '11.5' },
  ]);
  const unread = lines[0] ?? '';
  return { lines, ok: lines.length === 2 && /USDC/.test(unread) && !/\d/.test(unread.replace('USDC', '')) && !/NaN/.test(unread) && /XLM 12\.50/.test(lines[1] ?? '') };
});

await run('kyc', async () => {
  const { kycMessage } = await mod('./src/kyc.ts');
  const say = async (status: string) => kycMessage({ pollKycStatus: async () => status, pollKycDecision: async () => ({ status }) } as any, 'p1');
  const expired = await say('expired'), approved = await say('approved');
  return { expired, approved, ok: typeof expired === 'string' && expired.length > 0 && expired !== approved && approved === 'Verified' };
});

await run('trustline', async () => {
  const { enableUsdc } = await mod('./src/trust.ts');
  const calls: unknown[][] = [];
  const ok = await enableUsdc({ setTrustline: async (...a: unknown[]) => { calls.push(a); return { status: 'success' }; } } as any);
  const opts = calls[0]?.[1] as Record<string, unknown> | undefined;
  return { calls, ok: ok === true && calls.length === 1 && !(opts && ('sponsored' in opts || opts.skipSponsorship === true)) };
});

await run('ramp', async () => {
  const { bestTopUpRate } = await mod('./src/ramp.ts');
  const bodies: any[] = [];
  const quote = { quoteId: 'q1', expiresAt: '2026-12-01T00:00:00Z', amountIn: '10000', amountOut: '8', etaSeconds: 60, legs: [] };
  const fake: any = new Proxy({
    quoteRamp: async (b: unknown) => { bodies.push(b); return { quotes: [quote], rejected: [] }; },
    getRampRoutes: async () => ({ routes: [
      { direction: 'ONRAMP', fiat: { currency: 'ARS', country: 'AR', rail: 'BANK_TRANSFER' }, asset: { code: 'USDC', identifier: 'GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5', chain: 'STELLAR' } },
      { direction: 'ONRAMP', fiat: { currency: 'BRL', country: 'BR', rail: 'PIX' }, asset: { code: 'USDC', identifier: 'GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5', chain: 'STELLAR' } },
    ] }),
  }, { get: (t, k) => (k in t ? (t as any)[k] : k === 'then' ? undefined : () => { throw new Error(`unexpected call ${String(k)}`); }) });
  const rate = await bestTopUpRate(fake, 10000);
  const b = bodies[0] ?? {};
  const none = await bestTopUpRate({ ...fake, quoteRamp: async () => ({ quotes: [], rejected: [] }) } as any, 10000).catch((e: Error) => `throws: ${e.message}`);
  const bodyOk = b.direction === 'ONRAMP' && b.fiat?.currency === 'ARS' && b.fiat?.country === 'AR' && b.asset?.code === 'USDC' && b.asset?.chain === 'STELLAR' && Number(b.amount?.value) === 10000 && b.amount?.denomination === 'in';
  return { body: b, rate, none, ok: bodyOk && typeof rate === 'number' && Math.abs(rate - 1250) < 1 && none === null };
});

console.log(JSON.stringify(out));
