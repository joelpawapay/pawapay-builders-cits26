# Statements — async ledger export

The Statements API lets you request a CSV export of all wallet activity in a time range. The export is generated asynchronously; pawaPay POSTs a callback when it's ready, and the result is a pre-signed download URL.

## Endpoints

| Method | Path                              | Purpose                       | Signed? |
|--------|-----------------------------------|-------------------------------|---------|
| POST   | `/v2/statements`                  | Request a statement           | No      |
| GET    | `/v2/statements/{statementId}`    | Check status / fetch URL      | No      |

## State machine

```
ACCEPTED → PROCESSING → COMPLETED | FAILED
```

No `ENQUEUED` state. No `IN_RECONCILIATION` state. Statements are simpler.

## Request a statement — POST /v2/statements

### Request

```json
{
  "wallet": {
    "country": "ZMB",
    "currency": "ZMW",
    "provider": "MTN_MOMO_ZMB"
  },
  "callbackUrl": "https://merchant.com/statements/callback",
  "startDate": "2025-05-10T10:00:00",
  "endDate":   "2025-05-11T10:00:00",
  "compressed": false
}
```

### Field reference

- `wallet.country` (required) — ISO 3166-1 alpha-3.
- `wallet.currency` (required) — ISO 4217. Must match a wallet on the account.
- `wallet.provider` (optional) — only relevant when the account has per-provider wallets. Most accounts have a single per-country wallet — omit `provider`.
- `callbackUrl` (required) — HTTPS URL where pawaPay will POST when the statement is ready. Note: this is per-request — distinct from the deposit/payout callback URLs you set in the Dashboard.
- `startDate`, `endDate` (required) — RFC 3339 date-time. Maximum range **31 days**.
- `compressed` (optional, default `false`) — when `true`, the output is `.csv.gz`. When `false`, plain `.csv`.

### Response — 200

```json
{
  "statementId": "f4401bd2-1568-4140-bf2d-eb77d2b2b639",
  "status": "ACCEPTED",
  "created": "2025-05-15T08:00:00Z"
}
```

`status`: `ACCEPTED | REJECTED`.

### Failure codes (initiation)

`NO_AUTHENTICATION, AUTHENTICATION_ERROR, AUTHORISATION_ERROR, INVALID_INPUT, MISSING_PARAMETER, UNSUPPORTED_PARAMETER, INVALID_PARAMETER, INVALID_CALLBACK_URL, INVALID_DATE_RANGE, WALLET_NOT_FOUND`.

- `INVALID_DATE_RANGE` — `endDate` ≤ `startDate`, or range > 31 days.
- `INVALID_CALLBACK_URL` — not HTTPS or otherwise unreachable.
- `WALLET_NOT_FOUND` — the `wallet` triple doesn't match an existing wallet on the account.

## Check status — GET /v2/statements/{statementId}

```json
{
  "status": "FOUND",
  "data": {
    "statementId": "...",
    "status": "COMPLETED",
    "wallet": { "currency": "ZMW", "country": "ZMB", "provider": "MTN_MOMO_ZMB" },
    "created":   "2025-05-15T08:00:00Z",
    "startDate": "2025-05-10T10:00:00",
    "endDate":   "2025-05-11T10:00:00",
    "fileSize":  1048576,
    "downloadUrl": "https://pawapay.io/download/...",
    "downloadUrlExpiresAt": "2025-05-15T09:00:00Z",
    "completedAt": "2025-05-15T08:01:23Z"
  }
}
```

Top-level `status`: `FOUND | NOT_FOUND`. `data.status`: `PROCESSING | COMPLETED | FAILED`.

### Download URL semantics

- `downloadUrl` is a pre-signed URL. No auth header needed; just GET it.
- It expires at `downloadUrlExpiresAt`. After expiry, re-call `GET /v2/statements/{statementId}` — a fresh pre-signed URL is issued.
- File is plain `.csv` (or `.csv.gz` if `compressed: true`).
- `fileSize` is bytes.

### On FAILED

```json
{
  "status": "FOUND",
  "data": {
    "statementId": "...",
    "status": "FAILED",
    "failedAt": "2025-05-15T08:02:00Z",
    "failureReason": { "failureCode": "UNKNOWN_ERROR", "failureMessage": "..." }
  }
}
```

`failureReason.failureCode` is just `UNKNOWN_ERROR` (post-generation). Retry by submitting a new request.

## Statement callback

When the statement reaches `COMPLETED` (or `FAILED`), pawaPay POSTs to your `callbackUrl`. The callback body matches the `data` portion of the status-check response — `statementId`, `status`, `downloadUrl` (when COMPLETED), etc.

Acknowledge with HTTP 200. The same callback handling rules apply (idempotency, return 200 quickly, no auth gate, IP whitelist — see `references/callbacks.md`).

## CSV schema

The CSV columns vary slightly across providers/countries, but the universal headers are roughly:

- `Transaction ID` — pawaPay's transaction ID
- `Transaction Type` — DEPOSIT, PAYOUT, REFUND, REMITTANCE, TOPUP, FEE, etc.
- `Status` — COMPLETED, FAILED, etc.
- `Currency`
- `Amount`
- `Fee`
- `Net Amount`
- `Customer Phone Number`
- `Provider`
- `Client Reference` — your `clientReferenceId`
- `Created At`
- `Completed At`
- `Provider Transaction ID`

For the exact schema, generate one statement in sandbox and inspect — the schema can evolve.

## Pitfalls

- **Treating it as synchronous.** Don't poll in a tight loop expecting an immediate response — large date ranges can take minutes. Use the callback; fall back to polling at a slow cadence (e.g. every 30s) if no callback comes through.
- **Hitting the 31-day limit.** Chunk your reconciliation jobs to ≤31-day windows.
- **Letting `downloadUrl` expire.** Download immediately on receipt of the callback. If you store the URL for later, schedule a re-fetch via status-check before it expires.
- **Confusing this `callbackUrl` with the per-operation-type callbacks.** This URL is specified per-statement-request — it's not the Dashboard-configured callback URL.

## Use cases

- **End-of-day reconciliation**: schedule a statement at 00:01 covering the previous day. On callback, ingest the CSV and reconcile against your own ledger.
- **Investigation**: when a customer reports a missing deposit, run a statement for the relevant hour to see the raw ledger entries.
- **Compliance**: monthly statements for accounting and tax filings.
