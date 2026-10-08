# Errors, status enums, state machine, reconciliation

This is the bookkeeping reference. Read it whenever generating code that branches on a status field or handles a failure.

## The two-tier error model

Every initiation call returns a `status` field at HTTP 200 (most of the time). If that status is `REJECTED`, the response also carries a `failureReason` object:

```json
{ "failureReason": { "failureCode": "INVALID_AMOUNT", "failureMessage": "..." } }
```

There are two categories of `failureCode`:

1. **Technical / validation failures** — what's wrong with your request. Should not happen in production once your code is tested. Example: `INVALID_PHONE_NUMBER`, `MISSING_PARAMETER`.
2. **Transaction failures** — what's wrong with the customer's wallet or the MMO. Expected to happen during live operation. Example: `INSUFFICIENT_BALANCE`, `RECIPIENT_NOT_FOUND`.

`failureMessage` is intended for your developers / support team, NOT for the customer. Translate to a customer-friendly message in your UI.

## Technical failure codes (initiation-time)

| Code                              | HTTP | Where        | Meaning |
|-----------------------------------|------|--------------|---------|
| `NO_AUTHENTICATION`               | 401  | All          | `Authorization` header missing. |
| `AUTHENTICATION_ERROR`            | 403  | All          | Token invalid. |
| `AUTHORISATION_ERROR`             | 403  | All          | Token valid, not authorised for this endpoint. |
| `HTTP_SIGNATURE_ERROR`            | 403  | Signed ops   | Required signature missing or invalid. |
| `INVALID_INPUT`                   | 400  | All          | Body couldn't be parsed. |
| `MISSING_PARAMETER`               | 400  | All          | Required field missing — see `failureMessage`. |
| `UNSUPPORTED_PARAMETER`           | 400  | All          | Unknown field in body. |
| `INVALID_PARAMETER`               | 400  | All          | Value doesn't match the field's validation. |
| `DUPLICATE_METADATA_FIELD`        | 400  | All          | Same key appears twice in `metadata`. |
| `DEPOSITS_NOT_ALLOWED`            | 403  | Deposits     | Deposits not enabled on account. |
| `PAYOUTS_NOT_ALLOWED`             | 403  | Payouts      | Payouts not enabled. |
| `REFUNDS_NOT_ALLOWED`             | 403  | Refunds      | Refunds not enabled. |
| `REMITTANCES_NOT_ALLOWED`         | 403  | Remittances  | Remittances not enabled. |
| `AMOUNT_OUT_OF_BOUNDS`            | 200  | All          | Outside `minAmount`/`maxAmount` for that provider. |
| `INVALID_AMOUNT`                  | 200  | All          | Wrong decimal places. |
| `INVALID_PHONE_NUMBER`            | 200  | All          | MSISDN doesn't match the country/provider format. |
| `INVALID_CURRENCY`                | 200  | All          | Currency not supported by provider. |
| `INVALID_PROVIDER`                | 200  | All          | Provider code unknown or not enabled. |
| `PROVIDER_TEMPORARILY_UNAVAILABLE`| 200  | All          | Provider currently `CLOSED`. Check `availability`. |
| `INVALID_CALLBACK_URL`            | 400  | Statements   | Non-HTTPS or unreachable URL. |
| `INVALID_DATE_RANGE`              | 400  | Statements   | `endDate ≤ startDate` or range > 31 days. |
| `WALLET_NOT_FOUND`                | 400  | Statements   | Wallet triple doesn't match. |
| `PAWAPAY_WALLET_OUT_OF_FUNDS`     | 200  | Payouts/Refunds/Remittances | Insufficient funds at initiation. |
| `NOT_FOUND`                       | 200  | Refunds, resend-callback, fail-enqueued | Referenced transaction not found. |
| `INVALID_STATE`                   | 200  | Refunds, resend-callback, fail-enqueued | Transaction not in the expected state. |
| `AMOUNT_TOO_LARGE`                | 200  | Refunds      | Refund amount > remaining refundable. |
| `DEPOSIT_ALREADY_REFUNDED`        | 200  | Refunds      | Deposit fully refunded. |
| `REFUND_IN_PROGRESS`              | 200  | Refunds      | Another refund is processing for this deposit. |
| `UNKNOWN_ERROR`                   | 500  | All          | pawaPay internal issue. **Do not assume failure** — verify via status-check. |

## Transaction failure codes (post-processing — appear in callbacks and status-check)

| Code                              | Operations             | Meaning |
|-----------------------------------|------------------------|---------|
| `PAYMENT_NOT_APPROVED`            | Deposits               | Customer didn't enter PIN in time. |
| `INSUFFICIENT_BALANCE`            | Deposits               | Customer doesn't have enough funds. |
| `PAYMENT_IN_PROGRESS`             | Deposits               | Customer has another pending transaction. May take 10 min to clear. |
| `PAYER_NOT_FOUND`                 | Deposits               | MSISDN doesn't belong to the provider. |
| `PAYER_LIMIT_REACHED`             | Deposits               | Customer wallet limit reached. |
| `RECIPIENT_NOT_FOUND`             | Payouts/Refunds/Remittances | MSISDN doesn't belong to the provider. |
| `RECIPIENT_LIMIT_REACHED`         | Payouts                | Recipient wallet limit reached. |
| `WALLET_LIMIT_REACHED`            | All                    | Limit reached on the wallet (payer or recipient). |
| `MANUALLY_CANCELLED`              | Payouts/Refunds/Remittances | Cancelled via fail-enqueued or Dashboard. |
| `PAWAPAY_WALLET_OUT_OF_FUNDS`     | Payouts/Refunds/Remittances | Merchant wallet depleted mid-flight. |
| `DEPOSIT_ALREADY_REFUNDED`        | Refunds                | (Also a transaction failure.) |
| `AMOUNT_TOO_LARGE`                | Refunds                | (Also a transaction failure.) |
| `REFUND_IN_PROGRESS`              | Refunds                | (Also a transaction failure.) |
| `TRANSACTION_ALREADY_IN_PROCESS`  | Deposits (Kenya/Ethiopia) | A different transaction is already in flight on the same wallet. |
| `UNSPECIFIED_FAILURE`             | All                    | MMO failed without giving a reason. Retry with a new ID is generally safe. |
| `UNKNOWN_ERROR`                   | All                    | pawaPay internal. Verify via status-check. |

## Status enums by operation

| Operation   | Initiation status                            | Lifecycle status (status-check)                                          | Callback status                  |
|-------------|----------------------------------------------|--------------------------------------------------------------------------|----------------------------------|
| Deposit     | `ACCEPTED, REJECTED, DUPLICATE_IGNORED`      | `ACCEPTED, PROCESSING, IN_RECONCILIATION, COMPLETED, FAILED`             | `COMPLETED, PROCESSING, FAILED`  |
| Payout      | `ACCEPTED, REJECTED, DUPLICATE_IGNORED`      | `ACCEPTED, ENQUEUED, PROCESSING, IN_RECONCILIATION, COMPLETED, FAILED`   | `COMPLETED, PROCESSING, FAILED`  |
| Refund      | `ACCEPTED, REJECTED, DUPLICATE_IGNORED`      | `ACCEPTED, ENQUEUED, PROCESSING, IN_RECONCILIATION, COMPLETED, FAILED`   | `COMPLETED, PROCESSING, FAILED`  |
| Remittance  | `ACCEPTED, REJECTED, DUPLICATE_IGNORED`      | `ACCEPTED, ENQUEUED, PROCESSING, IN_RECONCILIATION, COMPLETED, FAILED`   | `COMPLETED, PROCESSING, FAILED`  |
| Statement   | `ACCEPTED, REJECTED`                         | `PROCESSING, COMPLETED, FAILED`                                          | (same body as status-check)      |

`ENQUEUED` exists only when the provider is `DELAYED` — deposits never enqueue.

`IN_RECONCILIATION` is automatic: pawaPay's reconciliation engine couldn't determine the final state from the MMO and is using alternative data sources. **No action required**; it resolves itself within minutes (longer for failures than successes).

`PROCESSING` in callbacks specifically means the REDIRECT_AUTH flow's `authorizationUrl` is ready — for non-REDIRECT_AUTH providers, you won't see callback `PROCESSING`.

## Defensive status handling pattern

The right shape for status checks, in pseudocode:

```python
def handle(record, txn):
    s = txn["status"]
    if s == "COMPLETED":
        record.mark_completed(txn)
    elif s == "FAILED":
        record.mark_failed(txn["failureReason"])
    elif s == "PROCESSING":
        record.note_processing()  # for REDIRECT_AUTH, capture authorizationUrl
    elif s == "ENQUEUED":
        record.note_enqueued()    # provider is delayed; show "in progress" to user
    elif s in ("ACCEPTED", "IN_RECONCILIATION"):
        record.note_pending()
    else:
        record.mark_needs_attention(s)  # unexpected — escalate to ops
```

The catch-all `else` is important. New states might be added; surfacing unknown states stops you silently mishandling them.

## The "don't mark FAILED prematurely" rule

This is the single most important pattern. Discrepancies between your system and pawaPay are almost always caused by marking something FAILED that actually succeeded — refunding a customer who already got paid, or charging a customer twice.

Only mark FAILED when:

1. The initiation response is `status: REJECTED` AND has a `failureReason`. **OR**
2. A callback or status-check returns `status: FAILED`. **OR**
3. Status-check returns `NOT_FOUND` AND the transaction was initiated ≥ 15 minutes ago.

In any other case — network errors, timeouts, 5xx, `UNKNOWN_ERROR`, ambiguous responses — leave the local record in `PENDING` and let the reconciliation cron resolve it later. Better to ask the customer to wait a few minutes than to double-pay them.

## The reconciliation cron (canonical pattern)

```python
def reconcile_pending():
    """Run every 2-5 minutes."""
    pending = db.get_transactions_pending_longer_than(minutes=15)
    for txn in pending:
        url = f"{BASE}/v2/{txn.operation}s/{txn.external_id}"
        try:
            r = requests.get(url, headers=AUTH_HEADER, timeout=10).json()
        except requests.RequestException:
            continue   # leave for next cycle

        if r["status"] == "FOUND":
            handle_status(txn, r["data"])   # see defensive pattern above
        elif r["status"] == "NOT_FOUND":
            db.mark_failed(txn.id, reason="never_reached_pawapay")
        # else: shouldn't happen, leave for next cycle
```

Run frequency matters less than reliability. 2-5 minutes is fine for most use cases. For very high-volume merchants, parallelise across workers.

## Handling network errors during initiation

```python
deposit_id = str(uuid.uuid4())
db.save(deposit_id, status="PENDING")  # 1. persist BEFORE call

try:
    r = requests.post(initiate_url, json=body, timeout=10)
    data = r.json()
except (requests.RequestException, ValueError):
    # 2. timeout OR malformed JSON: don't assume anything.
    return verify(deposit_id)

if data["status"] == "ACCEPTED":
    return {"state": "pending_callback"}
if data["status"] == "DUPLICATE_IGNORED":
    return verify(deposit_id)
if data["status"] == "REJECTED":
    db.update(deposit_id, status="FAILED", reason=data["failureReason"])
    return {"state": "failed", "reason": data["failureReason"]}

# Anything else (e.g. UNKNOWN_ERROR with no status):
return verify(deposit_id)

def verify(deposit_id):
    r = requests.get(f"{BASE}/v2/deposits/{deposit_id}", headers=AUTH_HEADER).json()
    if r["status"] == "NOT_FOUND":
        db.update(deposit_id, status="FAILED", reason="never_reached_pawapay")
        return {"state": "failed"}
    return r["data"]  # let the reconciler / callback handler advance it
```

## State machine cheat sheet

```
Deposit:      ACCEPTED → PROCESSING → (IN_RECONCILIATION) → COMPLETED | FAILED
                       └→ (REDIRECT_AUTH only: callback with PROCESSING + authorizationUrl)
Payout:       ACCEPTED → (ENQUEUED) → PROCESSING → (IN_RECONCILIATION) → COMPLETED | FAILED
Refund:       ACCEPTED → (ENQUEUED) → PROCESSING → (IN_RECONCILIATION) → COMPLETED | FAILED
Remittance:   ACCEPTED → (ENQUEUED) → PROCESSING → (IN_RECONCILIATION) → COMPLETED | FAILED
Statement:    ACCEPTED → PROCESSING → COMPLETED | FAILED
```

Terminal: `COMPLETED`, `FAILED`. Everything else is in flight.

## Mapping pawaPay statuses to user-facing messages

| pawaPay status        | User-facing message (suggested)                         | Action                                  |
|-----------------------|---------------------------------------------------------|-----------------------------------------|
| `ACCEPTED`/`PENDING`  | "Processing your payment"                               | Wait                                    |
| `PROCESSING`          | "Almost there"                                           | Wait (or redirect, for REDIRECT_AUTH)   |
| `ENQUEUED`            | "Your <provider> network is temporarily slow — we'll complete this when it's back up" | Wait |
| `IN_RECONCILIATION`   | "Your payment is being confirmed"                       | Wait (no action needed)                 |
| `COMPLETED`           | "Payment successful"                                    | Fulfil the order                        |
| `FAILED` + most codes | "Payment failed — please try again"                     | Show retry button                       |
| `FAILED` + `INSUFFICIENT_BALANCE` | "Your mobile money wallet doesn't have enough funds" | Show retry / topup info        |
| `FAILED` + `PAYER_NOT_FOUND` | "This phone number isn't registered with the chosen provider" | Show retry with provider override |
| `FAILED` + `PAYMENT_NOT_APPROVED` | "Payment wasn't authorised on time"                | Show retry                              |
| `FAILED` + `PROVIDER_TEMPORARILY_UNAVAILABLE` | "Network temporarily down — try another method or retry" | Suggest alternative provider |

`failureMessage` is for your support team. Don't show it to customers verbatim.
