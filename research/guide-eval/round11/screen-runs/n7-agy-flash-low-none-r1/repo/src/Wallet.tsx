import { useEffect, useState } from 'react';
import { usePollar } from '@pollar/react';
import { balanceLines } from './balances';
import { enableUsdc } from './trust';
import { bestTopUpRate } from './ramp';

export function Wallet() {
  const { isAuthenticated, wallet, login, walletBalance, refreshWalletBalance, getClient } = usePollar();
  const [rate, setRate] = useState<number | null>(null);

  useEffect(() => {
    if (wallet) void refreshWalletBalance();
  }, [wallet, refreshWalletBalance]);

  if (!isAuthenticated) return <button onClick={() => login({ provider: 'google' })}>Sign in to tip</button>;
  if (!wallet) return <p>Creating your wallet...</p>;

  return (
    <section>
      <p>Wallet: {wallet.address}</p>
      {walletBalance.step === 'loaded' && (
        <ul>
          {balanceLines(walletBalance.data.balances).map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}
      <button onClick={() => void enableUsdc(getClient())}>Accept USDC</button>
      <button onClick={async () => setRate(await bestTopUpRate(getClient(), 10_000))}>Add money</button>
      {rate !== null && <p>1 USDC = {rate} ARS</p>}
    </section>
  );
}
