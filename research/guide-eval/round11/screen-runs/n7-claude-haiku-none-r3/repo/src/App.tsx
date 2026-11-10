import { PollarProvider } from '@pollar/react';
import { pollarConfig } from './pollar';
import { Wallet } from './Wallet';

export function App() {
  return (
    <PollarProvider client={pollarConfig}>
      <Wallet />
    </PollarProvider>
  );
}
