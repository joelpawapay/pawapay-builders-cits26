# Authentication & signatures

Two layers: a bearer token (always required) and optional RFC 9421 message signatures (recommended for any production integration).

## Bearer token

Every request to the pawaPay Merchant API carries:

```
Authorization: Bearer <YOUR_API_TOKEN>
```

The token is generated in the pawaPay Dashboard (sandbox: `https://dashboard.sandbox.pawapay.io/`, production: `https://dashboard.pawapay.io/`). Sandbox and production tokens are different — generate a new one when promoting from sandbox to production.

Store tokens in your secrets manager / per-environment config. Never commit them.

### Failure codes

- `NO_AUTHENTICATION` (HTTP 401) — token missing from request headers.
- `AUTHENTICATION_ERROR` (HTTP 403) — token invalid or expired.
- `AUTHORISATION_ERROR` (HTTP 403) — token valid but lacks permission for this endpoint.
- `*_NOT_ALLOWED` (HTTP 403) — operation not enabled on the account (e.g. `DEPOSITS_NOT_ALLOWED`, `PAYOUTS_NOT_ALLOWED`).

## RFC 9421 signatures (recommended)

The second layer of security. If a token leaks, an attacker still can't initiate financial transactions because they don't have your private key. Signatures are applied **only** to financial-initiation endpoints.

### Which endpoints accept signatures

The OpenAPI spec declares the signature parameters on these endpoints:

- `POST /v2/deposits`
- `POST /v2/payouts`
- `POST /v2/payouts/bulk`
- `POST /v2/refunds`
- `POST /v2/remittances`
- `POST /v2/remittances/bulk`

Status-check (GET), fail-enqueued (POST), resend-callback (POST), statements, payment page, and toolkit endpoints do not require signatures.

### Enforcement

In `GET /v2/active-conf`, the `signatureConfiguration.signedRequestsOnly` boolean tells you whether your account is enforcing signatures. When `true`, unsigned financial-initiation calls are rejected with `HTTP_SIGNATURE_ERROR` (HTTP 401). Always check this field at app startup; behave accordingly.

### Headers attached to a signed request

```
Content-Digest:    sha-512=:<base64>:           # or sha-256
Signature-Date:    2024-05-02T15:36:45.058799Z  # ISO 8601 / RFC 3339
Signature:         sig-pp=:<base64>:
Signature-Input:   sig-pp=("@method" "@authority" "@path" "signature-date" "content-digest" "content-type");alg="ecdsa-p256-sha256";keyid="YOUR_KEY_ID";created=<unix>;expires=<unix>
Accept-Signature:  rsa-pss-sha512,ecdsa-p256-sha256,rsa-v1_5-sha256,ecdsa-p384-sha384
Accept-Digest:     sha-256,sha-512
```

`Accept-Signature` and `Accept-Digest` advertise which response signatures/digests the merchant can verify — pawaPay will pick from the list when signing the response.

### Allowed signature algorithms

Pick one — `ecdsa-p256-sha256` is the simplest and what pawaPay's reference Node implementation uses.

- `rsa-pss-sha512` — RSASSA-PSS with SHA-512
- `rsa-v1_5-sha256` — RSASSA-PKCS1-v1_5 with SHA-256
- `ecdsa-p256-sha256` — ECDSA P-256 with SHA-256 (recommended)
- `ecdsa-p384-sha384` — ECDSA P-384 with SHA-384

### Signing algorithm (recipe)

1. **Build the request body** (JSON). Don't mutate it after this point — sign the exact bytes you send.
2. **Compute `Content-Digest`**: `sha-512=:base64(sha512(body)):` (or sha-256). Format is literally `sha-512=:<base64>:` with colons.
3. **Pick a `created` and `expires` timestamp** (Unix seconds). Recommend `expires = created + 60`.
4. **Pick a key id** (`keyid`) — must match a public key you've registered in the Dashboard.
5. **Build the signature base** — a multi-line string with each component on its own line. Component order matches the `Signature-Input` covered list. The last line is `"@signature-params": <Signature-Input value without the label prefix>`.
6. **Sign the signature base** with your private key + selected algorithm. Base64-encode the signature output.
7. **Attach** `Content-Digest`, `Signature-Date`, `Signature`, `Signature-Input`, `Accept-Signature`, `Accept-Digest` to the request.

### Signature base example

For a `POST /v2/deposits` request:

```
"@method": POST
"@authority": api.pawapay.io
"@path": /v2/deposits
"signature-date": 2024-05-02T15:36:45.058799Z
"content-digest": sha-512=:mXRb9GJnfR/lyXOVfa27Wg+QrRgX3DVhXpQwjxbWoG3BgX7ZHmXLpvQb4il2kxgLjWmj6oSdwDdn5rUAJVYnUw==:
"content-type": application/json; charset=UTF-8
"@signature-params": ("@method" "@authority" "@path" "signature-date" "content-digest" "content-type");alg="ecdsa-p256-sha256";keyid="CUSTOMER_TEST_KEY";created=1714653405;expires=1714653465
```

### Reference implementations

- `scripts/sign_request.js` — Node, ECDSA P-256 + SHA-512.
- `scripts/sign_request.py` — Python, `cryptography` package, ECDSA P-256 + SHA-512.

When the user is in Node specifically, point them at pawaPay's own reference repo (`pawaPay/signatures-node-example`) on GitHub — they may already use it.

### Common signing pitfalls

- **Body bytes drift.** Serialise the JSON once, sign those exact bytes, send those exact bytes. If you re-serialise between sign and send, the `Content-Digest` mismatches.
- **Wrong `@authority`.** It's the `Host` value the server sees — for production `api.pawapay.io`, sandbox `api.sandbox.pawapay.io`. Not your URL.
- **Wrong `@path`.** Path only — no query string, no host. Starts with `/`.
- **Timezone in `Signature-Date`.** Use `Z` (UTC). Don't use local time.
- **`created`/`expires` skew.** Keep your server clock NTP-synced; pawaPay rejects expired signatures.
- **Mixed case in algorithm string.** Use exactly `ecdsa-p256-sha256`, lowercase, hyphenated.
- **Forgetting to include `content-type` in the covered list when you send a body.** It's recommended in the signature base.
- **Wrong key id.** `keyid` must match the registered identifier in the Dashboard exactly. Mismatches return `HTTP_SIGNATURE_ERROR`.

## Verifying signed callbacks (recommended)

When `signatureConfiguration.signedCallbacks = true` is enabled (via the Dashboard), every callback from pawaPay carries:

- `Content-Digest`
- `Signature-Date`
- `Signature`
- `Signature-Input`
- `Content-Type`

To verify:

1. Fetch the active public keys: `GET /v2/public-key/http` returns an array of `{ id, key }` (PEM-encoded).
2. Cache the keys — refresh on signature-verify failure or on a 24h timer.
3. On callback receipt, parse `Signature-Input`. The `keyid` parameter tells you which public key to use.
4. Reconstruct the signature base using the components listed in `Signature-Input`.
5. Verify the signature against the public key + signature base.
6. Verify the `Content-Digest` against the actual body bytes.
7. If either check fails, **reject the callback** (HTTP 401 or 4xx) — do not process the payload.

Reference implementation: `scripts/verify_callback.py`.

### Public-key endpoint shape

```json
GET /v2/public-key/http
→ 200
[
  {
    "id": "HTTP_EC_P256_KEY:1",
    "key": "-----BEGIN PUBLIC KEY-----\nMFkwE...==\n-----END PUBLIC KEY-----\n"
  }
]
```

Match the `keyid` in `Signature-Input` to the `id` here.

## Setting up signatures end-to-end (operational checklist)

1. Generate keypair locally. ECDSA P-256 is recommended:
   ```bash
   openssl ecparam -name prime256v1 -genkey -noout -out private.pem
   openssl ec -in private.pem -pubout -out public.pem
   ```
2. Upload `public.pem` to the pawaPay Dashboard (Settings → API tokens → Signatures). Assign it a key ID.
3. Store `private.pem` in your secrets manager — Vault, AWS Secrets Manager, GCP Secret Manager.
4. Update your initiation code to sign with the private key using the chosen `keyid`.
5. Enable "Signed requests" in the Dashboard. From this moment, unsigned calls are rejected.
6. (Optional) Enable "Signed callbacks" and start verifying signatures in your callback handler. Reference `scripts/verify_callback.py`.
7. Test in sandbox before flipping in production. Sandbox has a separate Dashboard, so repeat steps 1–6 for production.
