# Remittances — international / cross-border transfers

A remittance is a payout enriched with KYC fields: who is sending, their identification, the purpose of funds, the FX rate applied, etc. Required for cross-border money movement.

The remittance API is publicly documented only in the OpenAPI spec — there is no narrative guide. This reference is the most complete source.

## Endpoints

| Method | Path                                                   | Purpose                              | Signed? |
|--------|--------------------------------------------------------|--------------------------------------|---------|
| POST   | `/v2/remittances`                                      | Initiate a single remittance         | Yes     |
| POST   | `/v2/remittances/bulk`                                 | Initiate multiple remittances        | Yes     |
| GET    | `/v2/remittances/{remittanceId}`                       | Check status                         | No      |
| POST   | `/v2/remittances/fail-enqueued/{remittanceId}`         | Cancel an ENQUEUED remittance        | No      |
| POST   | `/v2/remittances/resend-callback/{remittanceId}`       | Re-trigger the final-state callback  | No      |

Account enablement: remittances must be enabled per-account. If not enabled you'll see `REMITTANCES_NOT_ALLOWED` (HTTP 403). Talk to pawaPay Sales.

## State machine

Same as payouts: `ACCEPTED → (ENQUEUED) → PROCESSING → (IN_RECONCILIATION) → COMPLETED | FAILED`.

## Initiate — POST /v2/remittances

### Full request body

```json
{
  "remittanceId": "afb57b93-7849-49aa-babb-4c3ccbfe3d79",
  "amount": "100",
  "currency": "ZMW",
  "customerMessage": "Family support",
  "metadata": [ { "transferRef": "TX-001" } ],

  "recipient": {
    "type": "MMO",
    "accountDetails": {
      "phoneNumber": "260763456789",
      "provider": "MTN_MOMO_ZMB"
    },
    "recipientDetails": {
      "firstName": "John",
      "lastName": "Doe"
    }
  },

  "sender": {
    "transactionDetails": {
      "transactionReference": "de83150a-5916-48a2-b048-bd85e022cb55",
      "originalAmount": "100",
      "originalCurrency": "USD",
      "buyFxRate": "23.88",
      "senderFees": "1",
      "purposeOfFunds": "FAMILY_SUPPORT",
      "sourceOfFunds": "SALARY"
    },
    "senderDetails": {
      "firstName": "Jane",
      "lastName": "Doe",
      "nationality": "USA",
      "phoneNumber": "12124567890",
      "address": {
        "addressLine": "1476 Sandhill Rd",
        "postalCode": "84058",
        "city": "Orem",
        "country": "USA"
      },
      "identification": {
        "type": "PASSPORT",
        "number": "E00007730"
      },
      "gender": "FEMALE",
      "dateOfBirth": "1977-12-31",
      "placeOfBirth": "USA",
      "occupation": "Project manager",
      "relationshipRecipient": "PARTNER"
    }
  }
}
```

### Field reference

#### Top level

- `remittanceId` (required) — UUIDv4. Idempotency key. Persist before calling.
- `amount`, `currency` (required) — the amount delivered to the recipient, in the recipient-country currency.
- `customerMessage`, `metadata` — same conventions as deposits/payouts.

#### `recipient`

- `type` (required) — `"MMO"`.
- `accountDetails.phoneNumber`, `accountDetails.provider` (required) — recipient's MMO account.
- `recipientDetails.firstName`, `recipientDetails.lastName` (required, max 64 chars each).

#### `sender.transactionDetails`

- `transactionReference` (required, max 64) — your reference for the transaction; appears in reporting and reconciliation.
- `originalAmount` (required, string) — amount in `originalCurrency` collected from the sender.
- `originalCurrency` (required) — ISO 4217. Sender-side currency (e.g. `"USD"`, `"EUR"`, `"GBP"`).
- `buyFxRate` (required, string) — the FX rate applied (originalCurrency → currency). String, decimal-precise.
- `senderFees` (required, string) — fees collected from the sender (in originalCurrency or your business model — be consistent).
- `purposeOfFunds` (required) — enum below.
- `sourceOfFunds` (required) — enum below.

#### `sender.senderDetails`

Required:

- `firstName`, `lastName` (max 64)
- `nationality` — ISO 3166-1 alpha-3 (e.g. `"USA"`, `"GBR"`, `"FRA"`)
- `phoneNumber` — free-form max 64 (NOT the strict MSISDN; just a contact phone)
- `address` — object with required `addressLine`, `postalCode`, `city`, `country` (ISO 3166-1 alpha-3)
- `identification` — `{ type, number }` — see ID types below

Optional:

- `gender` — `MALE | FEMALE | OTHER`
- `dateOfBirth` — ISO date `YYYY-MM-DD`
- `placeOfBirth` — max 64
- `occupation` — max 64
- `relationshipRecipient` — enum (see below)

### Enums

**`purposeOfFunds`**:
`FAMILY_SUPPORT, MEDICAL_EXPENSES, TUITION_FEES, EDUCATION_SUPPORT, GIFT_AND_OTHER_DONATIONS, HOME_IMPROVEMENT, DEBT_SETTLEMENT, REAL_ESTATE, TAXES, SALARY, SAVINGS, PERSONAL_TRANSFER, OTHER`

**`sourceOfFunds`**:
`SALARY, SAVINGS, LOTTERY, LOAN, BUSINESS_INCOME, GIFT, OTHER`

**`senderDetails.identification.type`**:
`NATIONAL_ID, PASSPORT, DRIVING_LICENSE, SOCIAL_SECURITY_ID, RESIDENCE_PERMIT`

**`senderDetails.gender`**:
`MALE, FEMALE, OTHER`

**`relationshipRecipient`** (a long list — copy-paste safe):
`FATHER, MOTHER, SON, DAUGHTER, BROTHER, SISTER, HUSBAND, WIFE, PARTNER, FRIEND, AUNT, UNCLE, COUSIN, NEPHEW, NIECE, GRANDFATHER, GRANDMOTHER, GRANDSON, GRANDDAUGHTER, STEPCHILD, DAUGHTER_IN_LAW, SON_IN_LAW, BORTHER_IN_LAW, SISTER_IN_LAW, MOTHER_IN_LAW, GUARDIAN, SELF`

**Note**: `BORTHER_IN_LAW` is a typo in the spec (should be `BROTHER_IN_LAW`). It is enforced literally — send `BORTHER_IN_LAW`, not the corrected spelling, until pawaPay fixes it.

### Response — 200

```json
{
  "remittanceId": "afb57b93-7849-49aa-babb-4c3ccbfe3d79",
  "status": "ACCEPTED",
  "created": "2025-05-15T07:38:56Z"
}
```

`status`: `ACCEPTED | REJECTED | DUPLICATE_IGNORED`.

### Failure code summary (initiation)

`NO_AUTHENTICATION, AUTHENTICATION_ERROR, AUTHORISATION_ERROR, HTTP_SIGNATURE_ERROR, INVALID_INPUT, MISSING_PARAMETER, UNSUPPORTED_PARAMETER, INVALID_PARAMETER, DUPLICATE_METADATA_FIELD, REMITTANCES_NOT_ALLOWED, INVALID_PHONE_NUMBER, INVALID_AMOUNT, AMOUNT_OUT_OF_BOUNDS, INVALID_CURRENCY, INVALID_PROVIDER, PROVIDER_TEMPORARILY_UNAVAILABLE, PAWAPAY_WALLET_OUT_OF_FUNDS, UNKNOWN_ERROR`.

`REMITTANCES_NOT_ALLOWED`: account doesn't have remittances enabled. Contact pawaPay Sales.

## Bulk — POST /v2/remittances/bulk

Array of `RemittanceInitiationRequest` in, array of `RemittanceCreationResponse` out. Each element independent. Same signing requirements.

## Check status — GET /v2/remittances/{remittanceId}

```json
{
  "status": "FOUND",
  "data": {
    "remittanceId": "...",
    "status": "COMPLETED",
    "amount": "100.00",
    "currency": "ZMW",
    "country": "ZMB",
    "recipient": {
      "type": "MMO",
      "accountDetails": { "phoneNumber": "...", "provider": "..." },
      "recipientDetails": { "firstName": "John", "lastName": "Doe" }
    },
    "sender": {
      "transactionDetails": { "transactionReference": "...", "originalAmount": "...", "originalCurrency": "...", "buyFxRate": "...", "senderFees": "...", "purposeOfFunds": "...", "sourceOfFunds": "..." },
      "senderDetails":      { "firstName": "...", "lastName": "...", "nationality": "...", "phoneNumber": "...", "address": {...}, "identification": {...} }
    },
    "customerMessage": "Family support",
    "created": "...",
    "providerTransactionId": "...",
    "failureReason": null,
    "metadata": { "transferRef": "TX-001" }
  }
}
```

`data.status`: `ACCEPTED, ENQUEUED, PROCESSING, IN_RECONCILIATION, COMPLETED, FAILED`.

The response includes both `recipient` and `sender` echoed back. Useful for reconciliation and audit.

## Lifecycle failure codes

Same as payouts: `PAWAPAY_WALLET_OUT_OF_FUNDS, RECIPIENT_NOT_FOUND, WALLET_LIMIT_REACHED, MANUALLY_CANCELLED, UNSPECIFIED_FAILURE, UNKNOWN_ERROR`.

## Cancel enqueued — POST /v2/remittances/fail-enqueued/{remittanceId}

Same shape and semantics as payout fail-enqueued. Only valid while status is `ENQUEUED`.

## Resend callback — POST /v2/remittances/resend-callback/{remittanceId}

Same shape and semantics as payout resend-callback. Remittance must be in a final state.

## Callback shape (remittance webhook)

```json
{
  "remittanceId": "...",
  "status": "COMPLETED",
  "amount": "100.00",
  "currency": "ZMW",
  "country": "ZMB",
  "recipient": {
    "type": "MMO",
    "accountDetails": {...},
    "recipientDetails": {...}
  },
  "sender": {
    "transactionDetails": {...},
    "senderDetails": {...}
  },
  "customerMessage": "Family support",
  "created": "...",
  "providerTransactionId": "...",
  "failureReason": null,
  "metadata": {...}
}
```

The remittance callback includes the `sender` block (required field) — unlike payout/deposit callbacks. Useful so the receiving system can reconcile against its own sender record.

`status` is the trimmed callback enum: `COMPLETED | PROCESSING | FAILED`.

## KYC / compliance notes

- **Truth of the data is on the merchant.** pawaPay does not verify the sender's ID document — it stores and reports the values. Merchants are responsible for collecting valid KYC and meeting their jurisdiction's AML rules.
- **`transactionReference` is your audit anchor.** It should be your internal transaction ID; appears in pawaPay statements and dashboards.
- **`buyFxRate` and `senderFees` are display values.** They appear in reporting and the customer's statements. They don't affect what pawaPay debits — pawaPay debits `amount` (in `currency`) from your wallet.

## Reduced example: minimal happy-path request

```json
{
  "remittanceId": "...",
  "amount": "5000",
  "currency": "NGN",
  "recipient": {
    "type": "MMO",
    "accountDetails": { "phoneNumber": "2348134567899", "provider": "MTN_MOMO_NGA" },
    "recipientDetails": { "firstName": "Adaeze", "lastName": "Okafor" }
  },
  "sender": {
    "transactionDetails": {
      "transactionReference": "TX-0001",
      "originalAmount": "3.50",
      "originalCurrency": "GBP",
      "buyFxRate": "1428.57",
      "senderFees": "0.30",
      "purposeOfFunds": "FAMILY_SUPPORT",
      "sourceOfFunds": "SALARY"
    },
    "senderDetails": {
      "firstName": "Chidi", "lastName": "Okafor",
      "nationality": "GBR",
      "phoneNumber": "447700900123",
      "address": { "addressLine": "10 Downing St", "postalCode": "SW1A 2AA", "city": "London", "country": "GBR" },
      "identification": { "type": "PASSPORT", "number": "537501234" }
    }
  }
}
```

## Pitfalls specific to remittances

- **Forgetting the typo `BORTHER_IN_LAW`.** Send it as-spelled until the spec is corrected.
- **`originalCurrency` confused with `currency`.** `originalCurrency` is the sender side; `currency` is the recipient side.
- **Missing nationality codes.** ISO 3166-1 alpha-3, not the 2-letter form. `USA` not `US`. `GBR` not `UK`.
- **Sending senderDetails.phoneNumber in strict MSISDN format.** The spec says max 64 chars, free-form — don't apply MSISDN sanitisation here. Only `recipient.accountDetails.phoneNumber` needs strict MSISDN.
- **Assuming remittances are enabled.** Check `active-conf` — providers expose a `REMITTANCE` operation type only if your account has it enabled for that provider.
