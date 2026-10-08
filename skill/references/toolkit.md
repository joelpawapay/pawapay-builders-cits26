# Toolkit endpoints

Helper endpoints for discovering configuration, validating phone numbers, checking provider availability, fetching balances, and getting public keys. None of these require signatures.

## GET /v2/active-conf — Account configuration

The most important read endpoint. Returns everything you need to dynamically configure your payment flows: which countries and providers are enabled, currencies, amount limits, decimal support, auth flow types, callback URLs, MMO status, PIN prompt instructions, etc.

### Query parameters

- `country` (optional) — ISO 3166-1 alpha-3. Filter to one country.
- `operationType` (optional) — `DEPOSIT | PAYOUT | REMITTANCE | PUSH_DEPOSIT | REFUND | NAME_LOOKUP`. Filter to one operation type.

### Response — 200

```json
{
  "companyName": "Acme Ltd",
  "signatureConfiguration": {
    "signedRequestsOnly": true,
    "signedCallbacks": true
  },
  "countries": [
    {
      "country": "RWA",
      "displayName": { "en": "Rwanda", "fr": "Rwanda" },
      "prefix": "250",
      "flag": "https://static-content.pawapay.io/country_flags/rwa.svg",
      "providers": [
        {
          "provider": "MTN_MOMO_RWA",
          "displayName": "MTN",
          "logo": "https://static-content.pawapay.io/company_logos/mtn.png",
          "nameDisplayedToCustomer": "Acme Ltd",
          "currencies": [
            {
              "currency": "RWF",
              "displayName": "R₣",
              "operationTypes": {
                "DEPOSIT": {
                  "authType": "PROVIDER_AUTH",
                  "pinPrompt": "AUTOMATIC",
                  "pinPromptRevivable": true,
                  "pinPromptInstructions": {
                    "channels": [
                      {
                        "type": "USSD",
                        "displayName": { "en": "Didn't get the PIN prompt?", "fr": "..." },
                        "quickLink": "tel*182*1*3%23",
                        "variables": { "shortCode": "*182*1*3#" },
                        "instructions": {
                          "en": [
                            { "text": "Dial *182*1*3# on your phone", "template": "Dial {{shortCode}} on your phone" },
                            { "text": "Enter PIN", "template": "Enter PIN" }
                          ],
                          "fr": [ ... ]
                        }
                      }
                    ]
                  },
                  "minAmount": "100",
                  "maxAmount": "2000000",
                  "decimalsInAmount": "NONE",
                  "status": "OPERATIONAL",
                  "callbackUrl": "https://merchant.com/depositCallback"
                },
                "PAYOUT":     { "minAmount": "100", "maxAmount": "2000000", "decimalsInAmount": "NONE", "status": "OPERATIONAL", "callbackUrl": "..." },
                "REFUND":     { "minAmount": "100", "maxAmount": "2000000", "decimalsInAmount": "NONE", "status": "OPERATIONAL", "callbackUrl": "..." },
                "REMITTANCE": { "minAmount": "100", "maxAmount": "2000000", "decimalsInAmount": "NONE", "status": "OPERATIONAL", "callbackUrl": "..." }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### Field reference

#### `signatureConfiguration`

- `signedRequestsOnly` — when `true`, all financial-initiation calls must be signed (otherwise rejected with `HTTP_SIGNATURE_ERROR`).
- `signedCallbacks` — when `true`, callbacks from pawaPay carry RFC 9421 signature headers.

Read this once at app startup and configure your signing/verification accordingly.

#### `countries[]`

- `country` — ISO 3166-1 alpha-3.
- `prefix` — country calling code (no `+`).
- `flag` — URL to an SVG flag asset.
- `displayName` — localised country names.

#### `providers[]`

- `provider` — provider code (`MTN_MOMO_RWA`, `MPESA_KEN`, etc.). Use in `payer.accountDetails.provider` / `recipient.accountDetails.provider`.
- `displayName` — short MMO name (e.g. `"MTN"`). For dropdown labels.
- `logo` — URL to logo asset. For dropdown icons.
- `nameDisplayedToCustomer` — what the customer sees on their PIN prompt / SMS. Show this on the waiting screen so the customer recognises it.

#### `currencies[].operationTypes[<operationType>]`

The per-operation configuration. Common fields:

- `minAmount`, `maxAmount` — strings, in the currency. Validate before initiation.
- `decimalsInAmount` — `TWO_PLACES | NONE`. Round amounts accordingly.
- `status` — `OPERATIONAL | DELAYED | CLOSED`. See `availability` below for the meanings.
- `callbackUrl` — the URL pawaPay POSTs to for this operationType. Set in the Dashboard; surfaced here.

DEPOSIT-only fields (PROVIDER_AUTH context):

- `authType` — `PROVIDER_AUTH | PREAUTH | REDIRECT_AUTH`.
- `pinPrompt` — `AUTOMATIC | MANUAL`. Only when `authType: PROVIDER_AUTH`.
- `pinPromptRevivable` — boolean. Customer can re-trigger the PIN prompt if missed.
- `pinPromptInstructions` — instructions block (channels, languages, USSD codes). Used for `MANUAL` prompts or revive UX.
- `authTokenInstructions` — instructions block, only when `authType: PREAUTH`. Steps for the customer to generate the OTP.

### `Instructions` block — shape

```json
{
  "channels": [
    {
      "type": "USSD",                                  // USSD | APP
      "displayName": { "en": "...", "fr": "..." },
      "quickLink": "tel*123#",                         // optional; use as <a href>
      "variables": { "shortCode": "*123#" },
      "instructions": {
        "en": [ { "text": "Dial *123# on your phone", "template": "Dial {{shortCode}} on your phone" } ],
        "fr": [ ... ]
      }
    }
  ]
}
```

`text` is pre-rendered; `template` + `variables` let you style key parts (e.g. bold the USSD code). Use `quickLink` as the `href` of a button so mobile customers can predial.

### Use it as the source of truth

The active-conf response IS your runtime config. Cache for a few minutes; refresh periodically. Don't hardcode provider lists, currencies, or limits — those evolve.

## GET /v2/availability — Provider operational status

A lighter-weight version of just the `status` field from active-conf.

### Query parameters

- `country` (optional) — ISO 3166-1 alpha-3.
- `operationType` (optional) — `DEPOSIT | PAYOUT | REMITTANCE | REFUND`.

### Response — 200

```json
[
  {
    "country": "GHA",
    "providers": [
      {
        "provider": "VODAFONE_GHA",
        "operationTypes": [
          { "operationType": "DEPOSIT", "status": "OPERATIONAL" },
          { "operationType": "PAYOUT",  "status": "DELAYED" }
        ]
      }
    ]
  }
]
```

### Status meanings

- `OPERATIONAL` — provider is up. Process normally.
- `DELAYED` — provider is degraded. Deposits initiated during `DELAYED` are rejected (`PROVIDER_TEMPORARILY_UNAVAILABLE`). Payouts/remittances/refunds are accepted and go to `ENQUEUED` until the provider recovers.
- `CLOSED` — provider is down. All operations are rejected (`PROVIDER_TEMPORARILY_UNAVAILABLE`).

Show this status to users up front so they can pick another provider or come back later.

## POST /v2/predict-provider — Validate phone number, predict provider

### Request

```json
{ "phoneNumber": "25007 834-56789a" }
```

Free-form input — pawaPay strips whitespace, special characters, leading zeros, and validates digit count for the country.

### Response — 200

```json
{
  "country": "RWA",
  "provider": "MTN_MOMO_RWA",
  "phoneNumber": "250783456789"
}
```

- `phoneNumber` — sanitised MSISDN. Use this verbatim in subsequent initiation calls.
- `provider` — most-likely provider. Accuracy is high but not 100% — let the user override in your UI.
- `country` — ISO 3166-1 alpha-3 of the predicted country.

### Failure shape

```json
{ "failureReason": { "failureCode": "INVALID_PARAMETER", "failureMessage": "Phone number does not match any provider's format" } }
```

Use this endpoint at every UI point where a user enters a phone number:
1. To sanitise the value.
2. To select the right provider automatically.
3. To validate the number before initiating.

## GET /v2/wallet-balances — Wallet balances

### Query parameters

- `country` (optional) — ISO 3166-1 alpha-3.

### Response — 200

```json
{
  "balances": [
    { "country": "ZMB", "balance": "21798.03", "currency": "ZMW", "provider": "" },
    { "country": "UGA", "balance": "10798.03", "currency": "UGX", "provider": "" }
  ]
}
```

- `provider` is empty string for the default per-country wallet; populated only when the account has per-provider wallets.
- `balance` is a decimal string in the wallet's currency. Use it as a precondition before initiating payouts/refunds/remittances.

Cache for a few seconds; not for minutes (balance moves in real time).

## GET /v2/public-key/http — Public keys for callback verification

### Response — 200

```json
[
  {
    "id": "HTTP_EC_P256_KEY:1",
    "key": "-----BEGIN PUBLIC KEY-----\nMFkwE...==\n-----END PUBLIC KEY-----\n"
  }
]
```

Used to verify the `Signature` header on inbound callbacks when `signedCallbacks: true` is enabled.

Match the `keyid` parameter in the callback's `Signature-Input` to the `id` here. Cache keys; refresh on a 24h timer or on verification failure.

See `references/auth.md` and `scripts/verify_callback.py` for verification details.

## Recipe: bootstrap your app config

At application startup:

1. `GET /v2/active-conf` → cache. Read `signatureConfiguration` to decide whether to sign.
2. `GET /v2/public-key/http` → cache. Use for callback verification.
3. `GET /v2/wallet-balances` → cache for a few seconds. Use as a precondition for payouts.

At each customer interaction:

1. `POST /v2/predict-provider` with the customer's raw input.
2. Look up the provider's config in cached active-conf (auth type, limits, decimals).
3. (Optional) Re-fetch `GET /v2/availability` to confirm current status.
4. Initiate the operation.

## Pitfalls

- **Caching active-conf forever.** Provider lists change. Refresh every few minutes (or every hour at most).
- **Hardcoding amounts.** Always use `minAmount`/`maxAmount` from active-conf — they're account-specific.
- **Ignoring `displayName`/`logo`.** These are designed for direct UI use. Don't curate your own mapping.
- **Skipping predict-provider.** Customers paste numbers with `+`, spaces, dashes, parentheses. Skipping sanitisation → `INVALID_PHONE_NUMBER` rejections in production.
