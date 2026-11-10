# fx-cli

Prints an exchange rate from our rates service.

    RATES_URL=https://rates.internal.example npx tsx src/main.ts USD EUR
    1 USD = 0.9214 EUR

The service answers `GET {RATES_URL}/rates/{BASE}` with JSON like
`{ "base": "USD", "date": "2026-11-02", "rates": { "EUR": 0.92141, "GBP": 0.78 } }`.
