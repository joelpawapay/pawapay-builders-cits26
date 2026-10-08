# Sandbox testing

The sandbox at `https://api.sandbox.pawapay.io` is functionally identical to production — same endpoints, same payloads, same signatures, same callback machinery. The two differences:

1. The customer doesn't enter a real PIN — transactions complete in seconds.
2. The outcome is determined by the last few digits of the test MSISDN you send.

Use these to exercise both happy paths and every failure code your system handles.

## Sandbox setup

1. Sign up at `https://dashboard.sandbox.pawapay.io/`. Sandbox accounts are issued instantly; no KYC needed.
2. Generate a sandbox API token. Sandbox tokens cannot call production and vice versa.
3. Set callback URLs in the Dashboard.
4. (Optional) Set up signatures in sandbox so you exercise the signing code paths.

Base URL: `https://api.sandbox.pawapay.io`.

## MSISDN suffix convention

For most providers, the last few digits of the test MSISDN determine the outcome. The suffix pattern is **consistent** across most providers, with small per-provider variations.

### Common suffix outcomes (most providers)

| Suffix | Operations | Status     | failureCode               |
|--------|-----------|------------|---------------------------|
| `019`  | Deposit   | `FAILED`   | `PAYER_LIMIT_REACHED`     |
| `029`  | Deposit   | `FAILED`   | `PAYER_NOT_FOUND`         |
| `039`  | Deposit   | `FAILED`   | `PAYMENT_NOT_APPROVED`    |
| `049`  | Deposit   | `FAILED`   | `INSUFFICIENT_BALANCE`    |
| `069`  | Deposit   | `FAILED`   | `UNSPECIFIED_FAILURE`     |
| `129`  | Both      | `SUBMITTED`| (stays pending)           |
| `789`  | Both      | `COMPLETED`| (success)                 |
| `089`  | Payout    | `FAILED`   | `RECIPIENT_NOT_FOUND`     |
| `099`  | Payout    | `FAILED`   | `WALLET_LIMIT_REACHED`    |
| `109`  | Payout    | `FAILED`   | `RECIPIENT_LIMIT_REACHED` |
| `119`  | Payout    | `FAILED`   | `UNSPECIFIED_FAILURE`     |

Some MMOs use slightly different suffixes (e.g. Mozambique Movitel uses `XX0` patterns, Burkina Faso providers use `XX8` patterns, Ethiopia and Kenya M-Pesa add suffix `059`/`050` for `TRANSACTION_ALREADY_IN_PROCESS`).

When in doubt, consult the per-country table at `https://docs.pawapay.io/v2/docs/test_numbers`.

## Per-country quick reference

These are the canonical happy-path numbers per country (suffix `...789` or country-specific). Use as a starting point.

| Country | Provider          | MSISDN          | Outcome   |
|---------|-------------------|-----------------|-----------|
| BEN     | MTN_MOMO_BEN      | `22951345789`   | COMPLETED |
| BEN     | MOOV_BEN          | `22995345789`   | COMPLETED |
| BFA     | MOOV_BFA          | `22602345678`   | COMPLETED |
| BFA     | ORANGE_BFA        | `22607345678`   | COMPLETED |
| CMR     | MTN_MOMO_CMR      | `237653456789`  | COMPLETED |
| CMR     | ORANGE_CMR        | `237693456789`  | COMPLETED |
| CIV     | MTN_MOMO_CIV      | `2250503456789` | COMPLETED |
| CIV     | ORANGE_CIV        | `2250734567890` | COMPLETED |
| COD     | VODACOM_MPESA_COD | `243813456789`  | COMPLETED |
| COD     | AIRTEL_COD        | `243973456789`  | COMPLETED |
| COD     | ORANGE_COD        | `243893456789`  | COMPLETED |
| ETH     | MPESA_ETH         | `251700000000`  | COMPLETED |
| GAB     | AIRTEL_GAB        | `24174345678`   | COMPLETED |
| GHA     | MTN_MOMO_GHA      | `233593456789`  | COMPLETED |
| GHA     | AIRTELTIGO_GHA    | `233273456789`  | COMPLETED |
| GHA     | VODAFONE_GHA      | `233503456789`  | COMPLETED |
| KEN     | MPESA_KEN         | `254703456789`  | COMPLETED |
| LSO     | MPESA_LSO         | `266100000000`  | COMPLETED |
| MWI     | AIRTEL_MWI        | `265993456789`  | COMPLETED |
| MWI     | TNM_MWI           | `265883456789`  | COMPLETED |
| MOZ     | MOVITEL_MOZ       | `258100000000`  | COMPLETED |
| NGA     | AIRTEL_NGA        | `2349034567899` | COMPLETED |
| NGA     | MTN_MOMO_NGA      | `2348134567899` | COMPLETED |
| COG     | AIRTEL_COG        | `242053456789`  | COMPLETED |
| COG     | MTN_MOMO_COG      | `242063456789`  | COMPLETED |
| RWA     | AIRTEL_RWA        | `250733456789`  | COMPLETED |
| RWA     | MTN_MOMO_RWA      | `250783456789`  | COMPLETED |
| SEN     | FREE_SEN          | `221763456789`  | COMPLETED |
| SEN     | ORANGE_SEN        | `221773456789`  | COMPLETED |
| SLE     | ORANGE_SLE        | `23276123456`   | COMPLETED |
| TZA     | AIRTEL_TZA        | `255683456789`  | COMPLETED |
| TZA     | VODACOM_TZA       | `255763456789`  | COMPLETED |
| TZA     | TIGO_TZA          | `255713456789`  | COMPLETED |
| TZA     | HALOTEL_TZA       | `255623456789`  | COMPLETED |
| UGA     | AIRTEL_OAPI_UGA   | `256753456789`  | COMPLETED |
| UGA     | MTN_MOMO_UGA      | `256783456789`  | COMPLETED |
| ZMB     | AIRTEL_OAPI_ZMB   | `260973456789`  | COMPLETED |
| ZMB     | MTN_MOMO_ZMB      | `260763456789`  | COMPLETED |
| ZMB     | ZAMTEL_ZMB        | `260953456700`  | COMPLETED |

To test a specific failure on any of these, replace the last 3 digits with the suffix from the table above. Example: `260763456049` triggers `INSUFFICIENT_BALANCE` on MTN ZMB deposits.

## Test plan to validate an integration

Run all these against your sandbox account before going live:

### Deposits
- Successful deposit (suffix `789`) → expect `ACCEPTED` then callback `COMPLETED`.
- `INSUFFICIENT_BALANCE` (suffix `049`) → callback `FAILED` with the code.
- `PAYMENT_NOT_APPROVED` (suffix `039`) → callback `FAILED`.
- `PAYER_NOT_FOUND` (suffix `029`) → callback `FAILED`.
- `PAYER_LIMIT_REACHED` (suffix `019`) → callback `FAILED`.
- Duplicate `depositId` → initiation response `DUPLICATE_IGNORED`.
- `INVALID_AMOUNT` — try `100.50` against a provider with `decimalsInAmount: NONE` (e.g. Benin MTN).
- `AMOUNT_OUT_OF_BOUNDS` — try `1` against a provider whose `minAmount` is `100`.
- `INVALID_PHONE_NUMBER` — send a bare 7-digit number with no country code.
- `INVALID_CURRENCY` — try `USD` on a provider that only accepts `RWF`.
- REDIRECT_AUTH flow — try a Wave SEN number, verify `nextStep: GET_AUTH_URL`, poll for `authorizationUrl`.
- PREAUTH flow — try an Orange BFA number with a `preAuthorisationCode` value.

### Payouts
- Successful payout → callback `COMPLETED`.
- `RECIPIENT_NOT_FOUND` (suffix `089`) → callback `FAILED`.
- `WALLET_LIMIT_REACHED` (suffix `099`) → callback `FAILED`.
- `UNSPECIFIED_FAILURE` (suffix `119`) → callback `FAILED`.
- `ENQUEUED` flow — simulate by initiating during a `DELAYED` state. (Sandbox doesn't trigger DELAYED on its own; the easier path is to verify status-check returns `ENQUEUED` from a fixture; for true testing, ask pawaPay support to flag a sandbox provider as DELAYED.)
- `MANUALLY_CANCELLED` — initiate a payout, then call `POST /v2/payouts/fail-enqueued/{payoutId}` while it's enqueued.
- Bulk payouts — submit an array with a mix of valid and invalid entries; verify each entry resolves independently.

### Refunds
- Successful refund on a `COMPLETED` deposit → callback `COMPLETED`.
- `AMOUNT_TOO_LARGE` — refund more than the deposit amount.
- `DEPOSIT_ALREADY_REFUNDED` — fully refund a deposit, then attempt another refund.
- `REFUND_IN_PROGRESS` — initiate two refunds for the same deposit in quick succession.
- `INVALID_STATE` — attempt to refund a `FAILED` or still-`PROCESSING` deposit.
- Partial refunds — multiple partials summing to less than the deposit total.

### Remittances
- Happy path with all KYC fields populated → callback `COMPLETED`.
- Missing required senderDetails field → initiation `REJECTED` with `MISSING_PARAMETER`.
- Invalid `purposeOfFunds` enum value → `INVALID_PARAMETER`.
- Bulk remittances.

### Signatures (if enabled)
- Signed deposit → succeeds.
- Same deposit with `signedRequestsOnly: true` but no signature headers → `HTTP_SIGNATURE_ERROR`.
- Same deposit with a tampered body → `HTTP_SIGNATURE_ERROR` (Content-Digest mismatch).
- Inbound callback with `signedCallbacks: true` — verify your handler validates the signature.

### Reconciliation
- Initiate a deposit, kill your callback handler before pawaPay can deliver. Wait 15+ minutes. Verify the reconciliation cron picks up the pending record, calls status-check, and marks it appropriately.
- Initiate a deposit, kill the request mid-flight (close the socket). Verify your code calls status-check and recovers gracefully.

## Tips

- **Faster sandbox.** Sandbox transactions complete in seconds. Production transactions can take 10-60 seconds (the customer needs time to enter their PIN). Don't time your retries on sandbox latency.
- **No real money.** Never use real customer phone numbers or amounts in sandbox.
- **One depositId per test.** Use a new UUIDv4 each time unless you're specifically testing `DUPLICATE_IGNORED`.
- **Configure sandbox callbacks separately from prod.** A tunnel (ngrok, Cloudflare Tunnel) is useful for local dev.
- **Use the `SUBMITTED`/`129` MSISDN** to test how your UI handles "still pending" states without forcing a status to resolve.
