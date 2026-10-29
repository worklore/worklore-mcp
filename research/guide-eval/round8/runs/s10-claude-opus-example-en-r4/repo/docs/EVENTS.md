# Product events — registration funnel

Owner: product. Status: approved, waiting for implementation.

We want to see where people drop out between opening the app and reading the
offers. Each row is one event. Names are snake_case and must match exactly,
dashboards and funnels are already built on them.

| Event | When | Properties |
|---|---|---|
| `registration_email_started` | User started typing their email | — |
| `registration_phone_started` | User started typing their phone number | — |
| `loan_amount_changed` | User moved the loan amount slider | `amount` (int, the chosen amount) |
| `terms_accepted` | User ticked the terms and conditions checkbox | — |
| `registration_continue_tapped` | User tapped Continue on the registration screen | `amount` (int), `terms` (bool) |
| `offers_scrolled` | User scrolled the offers list | `offset` (double, how far they scrolled) |

Notes
- Do not send the email or the phone number as properties (PII).
- Screen views are already tracked automatically, no event needed for those.
- The funnel is: email started → phone started → amount changed → terms
  accepted → continue tapped → offers scrolled.
