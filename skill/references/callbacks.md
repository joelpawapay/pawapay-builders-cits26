# Callbacks (webhooks) — receiving and handling

The pawaPay API is asynchronous. Once a transaction reaches a terminal state (`COMPLETED` or `FAILED`), pawaPay POSTs to your configured callback URL. This is the primary way to learn final state — polling is a fallback for missed callbacks.

## Setting up a callback URL

Configure per-operation-type callback URLs in the pawaPay Dashboard (Settings → System config → Callback URLs). Sandbox and production each have their own. The URLs you set appear in `active-conf` per operation type:

```json
"operationTypes": {
  "DEPOSIT": { "callbackUrl": "https://merchant.com/depositCallback", ... },
  "PAYOUT":  { "callbackUrl": "https://merchant.com/payoutCallback",  ... },
  "REFUND":  { "callbackUrl": "https://merchant.com/refundCallback",  ... }
}
```

You can use the same URL for all operations and dispatch internally on the body's ID field (`depositId` vs `payoutId` vs `refundId` vs `remittanceId`), or use different URLs per type.

For statements, the callback URL is per-request — see `references/statements.md`.

## Network requirements

- **HTTPS only**, with a certificate from a trusted CA (no self-signed).
- **Accept POST** with JSON body.
- **No auth gate** — pawaPay won't send your tokens. Either expose the endpoint publicly (with the signature verification below as the security boundary), or whitelist pawaPay's IPs **and** exempt them from any auth/WAF.
- Reachable from the public internet.

### IPs to whitelist

| Environment | IP                |
| ----------- | ----------------- |
| Sandbox     | `3.64.89.224/32`  |
| Production  | `18.192.208.15/32`|
| Production  | `18.195.113.136/32`|
| Production  | `3.72.212.107/32` |
| Production  | `54.73.125.42/32` |
| Production  | `54.155.38.214/32`|
| Production  | `54.73.130.113/32`|

These are stable as of mid-2025 but check `https://docs.pawapay.io/v2/docs/what_to_know#ips-to-whitelist` if a callback delivery fails.

## Delivery semantics

- pawaPay POSTs the JSON callback to your URL.
- Your handler must return HTTP **200** to acknowledge receipt. Any non-2xx response is treated as a delivery failure.
- On failure, pawaPay retries for up to **15 minutes** with exponential-ish backoff.
- After 15 minutes of failures, delivery stops. You can request a resend manually with `POST /v2/<op>/resend-callback/{id}` or from the Dashboard.

This means: **return 200 quickly even if your downstream processing is queued**. Do the heavy work async; just acknowledge the receipt fast.

## Callback body shapes

The shape mirrors the status-check `data` object, but with the trimmed `CallbackStatus` enum: `COMPLETED | PROCESSING | FAILED` only.

Also: `clientReferenceId` is **omitted** from deposit/payout/refund callbacks (it's present in status-check). Look it up locally by the transaction ID if you need it.

### Deposit callback

```json
{
  "depositId": "...",
  "status": "COMPLETED",
  "amount": "100.00",
  "currency": "RWF",
  "country": "RWA",
  "payer": { "type": "MMO", "accountDetails": { "phoneNumber": "...", "provider": "..." } },
  "customerMessage": "...",
  "created": "...",
  "providerTransactionId": "...",
  "failureReason": null,
  "metadata": { "orderId": "ORD-1" }
}
```

For REDIRECT_AUTH providers (Wave SEN/CIV), an additional callback arrives with `status: PROCESSING` and `nextStep: REDIRECT_TO_AUTH_URL`, populating `authorizationUrl` — this is your cue to redirect the customer.

### Payout callback

Same fields, but `payoutId` instead of `depositId`, and `recipient` instead of `payer`.

### Refund callback

Same fields, but `refundId` and `recipient`.

### Remittance callback

```json
{
  "remittanceId": "...",
  "status": "COMPLETED",
  "amount": "...",
  "currency": "...",
  "country": "...",
  "recipient": { "type": "MMO", "accountDetails": {...}, "recipientDetails": {...} },
  "sender":    { "transactionDetails": {...}, "senderDetails": {...} },
  "customerMessage": "...",
  "created": "...",
  "providerTransactionId": "...",
  "failureReason": null,
  "metadata": {...}
}
```

Remittance callbacks include the `sender` block (required field).

## Signature verification (when enabled)

When `signatureConfiguration.signedCallbacks: true` in active-conf, each callback carries RFC 9421 signature headers:

```
Content-Digest:  sha-512=:<base64>:
Signature-Date:  2024-05-02T16:45:51.131905Z
Signature:       sig-pp=:<base64>:
Signature-Input: sig-pp=("@method" "@authority" "@path" "signature-date" "content-digest" "content-type");alg="ecdsa-p256-sha256";keyid="HTTP_EC_P256_KEY:1";created=<unix>;expires=<unix>
Content-Type:    application/json; charset=UTF-8
```

Verification:

1. Read `Signature-Input`, extract `keyid` and the covered components.
2. Look up the public key from your cache of `GET /v2/public-key/http`. Refresh the cache on a miss.
3. Reconstruct the signature base by listing the components in the same order with their values from the request (case-sensitive header names, exact bytes).
4. Verify the signature using the public key + chosen algorithm.
5. Compute the `Content-Digest` of the body and compare to the header value.
6. If either check fails, **reject** the callback (HTTP 401 or 4xx) and do not process the body. Log the event for investigation.

Use `scripts/verify_callback.py` as the reference implementation.

### Note on `@authority` for inbound callbacks

The `@authority` in the signature base is the value of the `Host` header pawaPay sent — usually the merchant-configured callback URL's hostname. Use the host as observed in the request, not what you expect.

## Idempotency

Callbacks may be delivered more than once (e.g. if your 200 response was delayed and pawaPay's retry timer fired). Your handler MUST be idempotent.

Pattern:

1. Parse the body. Extract the transaction ID (`depositId`/`payoutId`/etc).
2. Look up your local record by that ID. If you've already processed a callback for this ID + status, return 200 immediately (no work).
3. Otherwise, persist the callback event (e.g. into an inbox table), update your record's state, fire downstream side effects.
4. Return 200.

The transaction ID is your dedupe key. Don't use `created` or other fields as the key — they aren't stable across resends.

## Handler design (Node example)

```javascript
import express from "express";
import { verifyCallback } from "./scripts/verify_callback.js";  // hypothetical port of the Python one

const app = express();
app.use(express.raw({ type: "application/json" }));  // keep raw bytes for signature verification

app.post("/pawapay/callback", async (req, res) => {
  // 1. Verify signature (only if signedCallbacks: true).
  try {
    await verifyCallback({
      method: "POST",
      authority: req.headers.host,
      path: req.path,
      headers: req.headers,
      bodyBytes: req.body,
      publicKeyResolver: getPawaPayPublicKey  // returns PEM for a given keyid
    });
  } catch (e) {
    return res.status(401).json({ error: "signature invalid" });
  }

  // 2. Parse.
  const payload = JSON.parse(req.body.toString("utf-8"));
  const txnId = payload.depositId || payload.payoutId || payload.refundId || payload.remittanceId;

  // 3. Idempotent persist.
  const existing = await db.callbacks.findByTxnId(txnId);
  if (existing && existing.status === payload.status) {
    return res.status(200).end();
  }

  // 4. Enqueue downstream processing; return 200 fast.
  await db.callbacks.upsert({ txnId, payload, receivedAt: new Date() });
  await queue.publish("pawapay.callback.received", { txnId });

  res.status(200).end();
});
```

```python
# Python (Flask) equivalent
from flask import Flask, request
app = Flask(__name__)

@app.post("/pawapay/callback")
def callback():
    raw = request.get_data()  # raw bytes for signature verification
    try:
        verify_callback(
            method="POST",
            authority=request.host,
            path=request.path,
            headers=request.headers,
            body_bytes=raw,
            public_key_resolver=get_pawapay_public_key
        )
    except Exception:
        return ("signature invalid", 401)

    payload = request.get_json()
    txn_id = payload.get("depositId") or payload.get("payoutId") or payload.get("refundId") or payload.get("remittanceId")
    if db.has_processed_callback(txn_id, payload["status"]):
        return ("", 200)
    db.save_callback(txn_id, payload)
    queue.publish("pawapay.callback.received", {"txnId": txn_id})
    return ("", 200)
```

## Resend a missed callback

If your callback handler missed an event (e.g. infrastructure was down), trigger a resend:

```
POST /v2/deposits/resend-callback/{depositId}
POST /v2/payouts/resend-callback/{payoutId}
POST /v2/refunds/resend-callback/{refundId}
POST /v2/remittances/resend-callback/{remittanceId}
```

Each returns either `{ status: "ACCEPTED" }` or `{ status: "REJECTED", failureReason: { failureCode: "NOT_FOUND" | "INVALID_STATE" } }`. The transaction must be in a final state.

## Reconciliation cron (always have one)

Callbacks fail. Networks blip, IPs change, deploys happen. A reconciliation cron catches what slips through:

```python
# Run every few minutes.
def reconcile():
    pending = db.get_transactions_pending_longer_than(minutes=15)
    for txn in pending:
        op = txn.operation  # "deposit"|"payout"|"refund"|"remittance"
        r = requests.get(f"{BASE}/v2/{op}s/{txn.id}",
                         headers={"Authorization": f"Bearer {TOKEN}"}).json()
        if r["status"] == "FOUND":
            handle_final_state(txn, r["data"])
        elif r["status"] == "NOT_FOUND":
            db.mark_failed(txn.id, reason="never_reached_pawapay")
        # else: leave for next cycle
```

## Pitfalls

- **Putting an authentication gate in front of the callback endpoint.** Either expose it publicly, or whitelist pawaPay's IPs and exempt them. Otherwise callbacks bounce silently.
- **Doing heavy work before returning 200.** Database writes / queue publishes only. Defer the rest.
- **Using `created` or `providerTransactionId` as idempotency key.** Use the merchant-supplied transaction ID.
- **Ignoring `status: PROCESSING` callbacks.** For REDIRECT_AUTH, that's your cue to redirect the customer.
- **Not verifying signatures.** If `signedCallbacks: true`, an unsigned callback is a forgery attempt.
- **Hardcoding pawaPay's IPs.** They can change. Use them as a defence-in-depth filter, not the sole authorisation.
- **Treating callbacks as ordered.** They aren't. A `FAILED` callback can in theory arrive after a `PROCESSING` one is still in flight. Handle defensively.
