# Providers — countries, MMOs, currencies, decimals, auth type

This is the static reference. **Always reconcile against the live `GET /v2/active-conf`** for amounts, currencies, status, and provider enablement — they change. Use this table to know which provider codes exist and roughly what to expect.

## Quick reading

- **Provider code** — pass as `provider` in `accountDetails`. Format usually `<MMO>_<ISO3>`.
- **Currency** — provider's working currency. ISO 4217. DRC providers support both `CDF` and `USD`.
- **Auth type** — DEPOSIT authorisation flow. `PROVIDER_AUTH` is the default (PIN prompt on phone).
- **Decimals** — `2` means `decimalsInAmount: TWO_PLACES`, `0` means `NONE`. Where deposits and payouts differ, both are noted.

| Country (ISO3) | Provider code           | Currency  | Auth         | Decimals (DEPO/PAYO)   |
|----------------|-------------------------|-----------|--------------|------------------------|
| BEN            | MTN_MOMO_BEN            | XOF       | PROVIDER_AUTH| 0 / 0                  |
| BEN            | MOOV_BEN                | XOF       | PROVIDER_AUTH| 0 / 0                  |
| BFA            | MOOV_BFA                | XOF       | PROVIDER_AUTH| 0 / 0                  |
| BFA            | ORANGE_BFA              | XOF       | PREAUTH      | 0 / 0                  |
| CMR            | MTN_MOMO_CMR            | XAF       | PROVIDER_AUTH| 0 / 0                  |
| CMR            | ORANGE_CMR              | XAF       | PROVIDER_AUTH| 0 / 0                  |
| CIV            | MTN_MOMO_CIV            | XOF       | PROVIDER_AUTH| 0 / 0                  |
| CIV            | ORANGE_CIV              | XOF       | PROVIDER_AUTH| 0 / 0                  |
| CIV            | WAVE_CIV                | XOF       | REDIRECT_AUTH| 0 / 0                  |
| COD            | VODACOM_MPESA_COD       | CDF / USD | PROVIDER_AUTH| CDF: 0 / USD: 2         |
| COD            | AIRTEL_COD              | CDF / USD | PROVIDER_AUTH| 2 / 2                  |
| COD            | ORANGE_COD              | CDF / USD | PROVIDER_AUTH| 2 / 2                  |
| ETH            | MPESA_ETH               | ETB       | PROVIDER_AUTH| 2 / 2                  |
| GAB            | AIRTEL_GAB              | XAF       | PROVIDER_AUTH| 2 / 2                  |
| GHA            | MTN_MOMO_GHA            | GHS       | PROVIDER_AUTH| 2 / 2                  |
| GHA            | AIRTELTIGO_GHA          | GHS       | PROVIDER_AUTH| 2 / 2                  |
| GHA            | VODAFONE_GHA            | GHS       | PROVIDER_AUTH| 2 / 2                  |
| KEN            | MPESA_KEN               | KES       | PROVIDER_AUTH| 0 / 2                  |
| LSO            | MPESA_LSO               | LSL       | PROVIDER_AUTH| 2 / 2                  |
| MWI            | AIRTEL_MWI              | MWK       | PROVIDER_AUTH| 2 / 2                  |
| MWI            | TNM_MWI                 | MWK       | PROVIDER_AUTH| 2 / 2                  |
| MOZ            | MOVITEL_MOZ             | MZN       | PROVIDER_AUTH| 0 / 2                  |
| MOZ            | VODACOM_MOZ             | MZN       | PROVIDER_AUTH| 2 / 2                  |
| NGA            | AIRTEL_NGA              | NGN       | PROVIDER_AUTH| 0 / 0                  |
| NGA            | MTN_MOMO_NGA            | NGN       | PROVIDER_AUTH| 2 / 2                  |
| COG            | AIRTEL_COG              | XAF       | PROVIDER_AUTH| 0 / 0                  |
| COG            | MTN_MOMO_COG            | XAF       | PROVIDER_AUTH| 0 / 0                  |
| RWA            | AIRTEL_RWA              | RWF       | PROVIDER_AUTH| 0 / 0                  |
| RWA            | MTN_MOMO_RWA            | RWF       | PROVIDER_AUTH| 0 / 0                  |
| SEN            | FREE_SEN                | XOF       | PROVIDER_AUTH| 0 / 0                  |
| SEN            | ORANGE_SEN              | XOF       | PROVIDER_AUTH| 0 / 0                  |
| SEN            | WAVE_SEN                | XOF       | REDIRECT_AUTH| 0 / 0                  |
| SLE            | ORANGE_SLE              | SLE       | PROVIDER_AUTH| 2 / 2                  |
| TZA            | AIRTEL_TZA              | TZS       | PROVIDER_AUTH| 2 / 2                  |
| TZA            | VODACOM_TZA             | TZS       | PROVIDER_AUTH| 0 / 0                  |
| TZA            | TIGO_TZA                | TZS       | PROVIDER_AUTH| 0 / 0                  |
| TZA            | HALOTEL_TZA             | TZS       | PROVIDER_AUTH| 0 / 0                  |
| UGA            | AIRTEL_OAPI_UGA         | UGX       | PROVIDER_AUTH| 0 / 0                  |
| UGA            | MTN_MOMO_UGA            | UGX       | PROVIDER_AUTH| 2 / 2                  |
| ZMB            | AIRTEL_OAPI_ZMB         | ZMW       | PROVIDER_AUTH| 2 / 2                  |
| ZMB            | MTN_MOMO_ZMB            | ZMW       | PROVIDER_AUTH| 2 / 2                  |
| ZMB            | ZAMTEL_ZMB              | ZMW       | PROVIDER_AUTH| 2 / 2                  |

## Authorisation types

### PROVIDER_AUTH (overwhelmingly common)

Customer's MMO sends a PIN prompt to their phone. Customer enters PIN; payment completes. Sub-variants:

- `pinPrompt: AUTOMATIC` — the prompt pops up by itself.
- `pinPrompt: MANUAL` — customer must dial a USSD code first (shown via `pinPromptInstructions`).
- `pinPromptRevivable: true` — if the prompt is missed, customer can re-trigger it.

### PREAUTH (Orange Burkina Faso)

Customer dials a USSD menu, generates an OTP, gives the OTP to your UI; you send it as `preAuthorisationCode` in the deposit request. Get the steps from `authTokenInstructions` in active-conf.

### REDIRECT_AUTH (Wave SEN, Wave CIV)

Customer is redirected to a Wave-hosted page (or scans a QR with the Wave app on their phone). After paying, they bounce back to `successfulUrl`/`failedUrl`.

Flow:
1. Pass `successfulUrl` + `failedUrl` in the deposit request.
2. Initiation response has `nextStep: GET_AUTH_URL`.
3. Poll status-check (or wait for the `PROCESSING` callback) until `authorizationUrl` is populated.
4. Redirect customer to `authorizationUrl`.

## Currency notes

- **XOF** (West African CFA franc) — Benin, Burkina Faso, Côte d'Ivoire, Senegal.
- **XAF** (Central African CFA franc) — Cameroon, Gabon, Republic of the Congo. Same exchange rate as XOF historically, different ISO code.
- **DRC supports both `CDF` and `USD`.** Other countries are single-currency.
- **SLE** (Sierra Leone leone) — note this is the post-2022 redenomination code. Older code `SLL` is no longer used.
- **All amounts are decimal strings** regardless of currency. Round to the provider's `decimalsInAmount`.

## Country calling codes (used in MSISDN sanitisation)

| ISO3 | Calling code |
|------|--------------|
| BEN  | 229 |
| BFA  | 226 |
| CMR  | 237 |
| CIV  | 225 |
| COD  | 243 |
| COG  | 242 |
| ETH  | 251 |
| GAB  | 241 |
| GHA  | 233 |
| KEN  | 254 |
| LSO  | 266 |
| MWI  | 265 |
| MOZ  | 258 |
| NGA  | 234 |
| RWA  | 250 |
| SEN  | 221 |
| SLE  | 232 |
| TZA  | 255 |
| UGA  | 256 |
| ZMB  | 260 |

But: rely on `predict-provider` to detect and sanitise. These codes are for sanity checks only.

## Pitfalls when picking a provider

- **Don't default-select a provider.** The customer has one specific MMO; getting it wrong forces them to know to change it. Either use `predict-provider`'s output as the default (with override allowed), or force an explicit choice.
- **`MOOV_BEN` is on the same number range as `MTN_MOMO_BEN`.** `predict-provider` can't always tell them apart from MSISDN alone. Always allow override.
- **Provider codes are not stable across versions.** v1 had different codes (e.g. `MTN_ZMB`). v2 uses fully-qualified codes. Don't share provider strings between v1 and v2 code paths.
- **Same MMO, different country = different code.** `MTN_MOMO_ZMB` ≠ `MTN_MOMO_RWA`. There's no generic "MTN" code.
- **MMOs go through rebrands.** `AIRTELTIGO_GHA` was previously branded AT; might be renamed again. Don't show the raw provider code to customers — use `displayName` from active-conf.
- **Wave shows as one logo across multiple countries.** Use `nameDisplayedToCustomer` from active-conf to render UI consistent with what shows on the customer's phone.

## When new countries / providers launch

pawaPay adds new MMOs and countries periodically. Your code stays correct if you:

1. Read provider list from `active-conf` rather than hardcoding.
2. Render `displayName` / `logo` from active-conf.
3. Handle unknown `provider` codes gracefully in your customer-support tooling (don't crash; log + escalate).

Then a new MMO can be enabled in your Dashboard, appear in `active-conf`, and start working without code changes.
