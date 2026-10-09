---
name: pawapay-merchant-api-v2
description: Build production-grade integrations with the PawaPay Merchant API v2 — deposits, payouts, refunds, remittances, payment page, statements, and the toolkit endpoints (active-conf, predict-provider, availability, wallet-balances, public-keys). Covers RFC 9421 request signing, signed callback verification, UUIDv4 idempotency, the async state machine, the three deposit auth flows (PIN prompt, PREAUTH OTP, REDIRECT_AUTH for Wave), reconciliation cycles, callback handler design, and sandbox testing. Use this skill whenever the user mentions PawaPay, pawapay, mobile money in Africa, MMO, MTN MoMo, M-Pesa, Airtel Money, Orange Money, Vodacom, Wave, the merchant API, or any of the v2 endpoints (deposits, payouts, refunds, remittances, statements, active-conf, predict-provider, availability) — even when they don't name the skill explicitly. Also when working in any language (Node, Python, Go, Java, PHP, Ruby, React, etc.) on payment flows that touch PawaPay.
---

# PawaPay Merchant API v2

This skill is a working reference for the PawaPay Merchant API v2 — the pan-African mobile money gateway connecting merchants to MMOs (MTN MoMo, M-Pesa, Airtel Money, Orange, Vodacom, Wave, etc.) across ~20 countries.

It is designed for agentic developers building real integrations. Read the reference files for each area before generating code; the goal is for code to work first time against the sandbox without further docs lookup.

## When this skill applies

Use it for any code that calls `api.sandbox.pawapay.io` or `api.pawapay.io`, any callback handler receiving PawaPay webhooks, any RFC 9421 signing or verification work tied to PawaPay, or any data modelling around the PawaPay state machine.

## Core architectural facts

These shape every integration. Internalise them before writing code.

**The API is asynchronous.** Initiation calls return `ACCEPTED` (or `REJECTED`/`DUPLICATE_IGNORED`). The final state (`COMPLETED` or `FAILED`) arrives later via callback, or by polling the status-check endpoint. Never assume "ACCEPTED" means "money moved".

**Every transaction has a merchant-supplied UUIDv4 ID.** `depositId`, `payoutId`, `refundId`, `remittanceId`, `statementId`. The merchant generates and **persists this ID before** calling PawaPay so that if the network blips mid-call, the merchant can still ask "did you receive my request?" via the status-check endpoint. Reusing an ID returns `DUPLICATE_IGNORED` — this is the idempotency mechanism.

**Amounts are strings.** Never floats. Pattern `^([0]|([1-9][0-9]{0,17}))([.][0-9]{0,3}[1-9])?$`. Whether decimals are allowed depends on the provider (`decimalsInAmount: NONE | TWO_PLACES`) — discover it from `/v2/active-conf`.

**Phone numbers are MSISDN format**: digits only, full country code, no leading `+`, no leading `0`, no spaces. Always run customer input through `POST /v2/predict-provider` before initiation — it sanitises the number and predicts the provider.

**Providers can be unavailable.** `GET /v2/availability` (or the `status` field in active-conf) returns `OPERATIONAL | DELAYED | CLOSED` per provider per operation type. For payouts/remittances/refunds, `DELAYED` causes PawaPay to **enqueue** the transaction (you'll see status `ENQUEUED`) and process when the provider recovers. Deposits don't queue — they're rejected during `CLOSED` with `PROVIDER_TEMPORARILY_UNAVAILABLE`.

**Signatures are optional but recommended.** Initiation endpoints (deposits, payouts, refunds, remittances + their bulk variants) accept RFC 9421 message signatures (`Content-Digest`, `Signature`, `Signature-Input`, `Accept-Signature`, `Accept-Digest`). When the account has `signatureConfiguration.signedRequestsOnly = true`, signatures are enforced — unsigned requests are rejected with `HTTP_SIGNATURE_ERROR`. Callbacks can also be signed by PawaPay (verify them using keys from `GET /v2/public-key/http`).

**Sandbox is functionally identical to production**, except for the base URL, the API token, and that the customer's PIN prompt step is skipped (transactions complete in seconds rather than minutes). Use the sandbox MSISDNs (see `references/testing.md`) to simulate every outcome.

## Decision tree — which reference do you need?

Read each reference file fully before writing the corresponding code. They contain endpoint specs, full schemas, error codes, and idiomatic patterns.

- **Authentication & signatures (every integration starts here)** → `references/auth.md`
- **Collect money from a customer** → `references/deposits.md`
- **Send money to a customer** → `references/payouts.md` (includes bulk + enqueued handling)
- **Refund a previous deposit** → `references/refunds.md` (full + partial)
- **Cross-border / international transfer with KYC** → `references/remittances.md`
- **Hosted checkout (no UI to build)** → `references/payment_page.md`
- **Account statements / reconciliation files** → `references/statements.md`
- **Discovering providers, countries, limits, decimals, callback URLs, MMO availability, validating phone numbers, fetching public keys, checking wallet balances** → `references/toolkit.md`
- **Receiving webhooks (signature verify, idempotency, IP whitelist)** → `references/callbacks.md`
- **Error codes, status enums, state machine, defensive handling, reconciliation cycle** → `references/errors.md`
- **Sandbox testing (the special MSISDN suffix system per provider)** → `references/testing.md`
- **Which providers and currencies are supported in which country (decimal support, auth type)** → `references/providers.md`

## Reusable scripts

These are reference implementations of the trickiest bit — RFC 9421 signing and verification. Use them directly when the user's language matches, or use them as the source of truth when porting to another language.

- `scripts/sign_request.js` — Sign an outbound request body with ECDSA P-256 (Node).
- `scripts/sign_request.py` — Same, in Python (`cryptography` library).
- `scripts/verify_callback.py` — Verify the signature on an inbound callback against PawaPay's public key (Python).

## Building a first-time-correct integration — recipe

When the user asks for "build a deposit/payout/etc. flow in <language>", the implementation should follow this order. **Read the relevant reference file first** so the generated code captures every detail.

1. **Pick environment.** Base URL = `https://api.sandbox.pawapay.io` for dev, `https://api.pawapay.io` for prod. Store as env var; never hardcode.
2. **Acquire API token** from the PawaPay Dashboard (sandbox or production dashboard, they're separate). Bearer token in `Authorization` header on every call.
3. **(Optional but recommended) Set up signing.** Generate an ECDSA P-256 keypair, upload the public key to the PawaPay Dashboard, keep the private key in your secrets manager. Sign all financial-initiation calls using the pattern in `scripts/sign_request.*`. See `references/auth.md`.
4. **Set up the callback handler endpoint.** HTTPS, public, idempotent, returns HTTP 200 on success, accepts PawaPay's IP range, no auth gate (or one that exempts PawaPay). Register the URL per operation type in the Dashboard. See `references/callbacks.md`.
5. **Generate a UUIDv4 transaction ID and persist it** before any initiation call. Pattern: store the local record with `status=PENDING` and the PawaPay ID, then make the API call.
6. **Initiate** — POST to `/v2/deposits`, `/v2/payouts`, etc. Inspect the response's `status` field. Handle `ACCEPTED`, `REJECTED` (read `failureReason.failureCode`), `DUPLICATE_IGNORED`, and the no-response (timeout) case by calling the status-check endpoint.
7. **Wait for callback OR poll status-check** until terminal state (`COMPLETED` or `FAILED`).
8. **Implement a reconciliation cycle**: every few minutes, find local records that have been pending > 15 min and call the status-check endpoint to resolve them. See the `references/errors.md` reconciliation pattern.
9. **Defensive status handling**: explicit checks for `COMPLETED`, `FAILED`, `PROCESSING`, `ENQUEUED`, `IN_RECONCILIATION` — everything else escalates as `NEEDS_ATTENTION`. Never assume an absent status means failure.

## Idiomatic patterns to use across languages

These show up repeatedly. Don't reinvent.

**UUID generation.** Node: `crypto.randomUUID()`. Python: `uuid.uuid4()`. Go: `github.com/google/uuid`. Java: `UUID.randomUUID()`. PHP: `Ramsey\Uuid\Uuid::uuid4()`. Always v4. Always lowercase. Always 36-char canonical hyphenated form.

**Amount as decimal-string.** Never floats. Use `BigDecimal`, Python `decimal.Decimal`, JS `decimal.js`, Go `shopspring/decimal`. Only stringify at the final API boundary, with rounding to the provider's `decimalsInAmount` (NONE → 0 dp, TWO_PLACES → 2 dp).

**HTTP client.** Use the boring choice: `fetch`/`axios` in Node, `httpx` or `requests` in Python, `net/http` in Go. Set explicit timeouts (5–10s for initiation, 3–5s for status-check). Treat HTTP 5xx and timeouts as "status unknown" — do not retry blindly; call status-check first.

**Retries.** Idempotent endpoints (status-check, active-conf) are safe to retry with exponential backoff. Initiation endpoints are *also* safe to retry with the same `<txn>Id` (you'll get `DUPLICATE_IGNORED` if the first call landed) — but always cap retries and bias toward status-check on timeout.

**Callback handlers should be lean.** Validate signature, persist the event with the PawaPay txnId as the dedupe key, return 200, do the heavy work asynchronously. PawaPay retries failed deliveries for 15 minutes — return 200 even if downstream processing is queued.

## Common pitfalls — call these out when generating code

- Floating-point amounts. Always strings.
- Hardcoded provider lists. Always pull from `/v2/active-conf`.
- Default-selected provider in a UI dropdown. Causes massive failure rates — let the customer choose, or use predict-provider's output.
- Forgetting `IN_RECONCILIATION` is not a final state. The reconciler will resolve it; no action needed.
- Treating callback status `PROCESSING` as a final state. For REDIRECT_AUTH providers (Wave), `PROCESSING` is the moment the `authorizationUrl` is ready — redirect the customer.
- Missing reconciliation cron. Callbacks fail (network, deploys, IP changes) and the system silently leaks pending transactions. Always have a recheck cycle for stale pendings.
- Putting auth in front of the callback endpoint, then forgetting to whitelist PawaPay's IPs. Callbacks fail silently.
- Sending `+` or spaces in the `phoneNumber` field. Run input through `predict-provider` first.
- Assuming all providers support decimals. They don't — Benin's MTN/Moov are integer-only. Check `decimalsInAmount`.

## Open questions / things this skill does NOT cover

- **Name lookup**: as of the v2 OpenAPI spec, `NAME_LOOKUP` exists only as an `operationType` enum value in `/v2/active-conf` (so providers can declare support), but there is no public `/v2/name-lookup` endpoint. If the user needs name lookup, point them at PawaPay support to confirm availability and capture the call shape — the skill can't generate code for it yet.
- **Payment Page field-name ambiguity**: the OpenAPI spec uses `phoneNumber` and `amountDetails.{amount,currency}` in `POST /v2/paymentpage` requests; some public-doc examples use `msisdn` and a top-level `amount`. The spec is authoritative; test in sandbox if a customer reports otherwise. See `references/payment_page.md`.
- **Dashboard-side configuration** (creating tokens, setting callback URLs, uploading public keys, enabling signed callbacks, configuring IP whitelist) — this skill assumes those are already done. Direct the user to `https://dashboard.sandbox.pawapay.io/` and `https://dashboard.pawapay.io/`.

## How to use this skill in practice

When a user asks for help on a PawaPay task:

1. **Read the relevant reference file.** Don't generate from memory — the field-name details (`amountDetails` vs `amount`, `accountDetails` vs `address`) and the failure-code enums matter for getting code that works first time.
2. **Check whether signatures are needed.** If the user's account has `signedRequestsOnly: true`, sign every financial-initiation call. The script in `scripts/sign_request.*` is the reference implementation.
3. **Pick a language idiom and write directly.** Don't generate a wrapper "SDK"; PawaPay's API surface is small enough that direct HTTP calls are clearer than abstraction.
4. **Always include**: env-var-based config, a UUIDv4 generator, structured error handling on the response's `status` field, and at least a stub for the callback handler.
5. **Mention sandbox testing.** Point the user at `references/testing.md` for the special MSISDNs that simulate each failure mode.

If the user is in doubt about which provider/currency/limit to use, run them through `/v2/active-conf` (and `references/toolkit.md`) — never invent a value.
