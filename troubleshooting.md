# Troubleshooting and FAQ

Find your error code below. PawaPay puts it in `failureReason.failureCode` on every failed response. The full list is on PawaPay's [failure codes page](https://docs.pawapay.io/v2/docs/failure_codes).

## PawaPay rejected the request

These come back straight away with status `REJECTED`, or as an error body with no status. Nothing reached the customer, so fix the request and send it again with a new ID.

| Code | Cause | Fix |
| --- | --- | --- |
| `NO_AUTHENTICATION` | No `Authorization` header | Send `Authorization: Bearer <token>` |
| `AUTHENTICATION_ERROR` | The token is wrong | Check for a missing character or extra space. Use a sandbox token with `api.sandbox.pawapay.io` |
| `AUTHORISATION_ERROR` | The token can't call this endpoint | Ask Joel |
| `MISSING_PARAMETER` | A required field is missing | `failureMessage` names the field |
| `INVALID_PARAMETER` | A field has the wrong format | Read `failureMessage`. Check the ID is a UUIDv4 and `customerMessage` is 4 to 22 letters, digits, or spaces |
| `UNSUPPORTED_PARAMETER` | A field name PawaPay doesn't know | Check spelling and nesting against the examples |
| `INVALID_INPUT` | The body isn't valid JSON | Send `Content-Type: application/json` and a JSON body |
| `INVALID_AMOUNT` | Decimals on an XAF amount | Send `"1000"`, not `"1000.50"` |
| `AMOUNT_OUT_OF_BOUNDS` | Amount below the minimum or above the maximum | Read the limits from `GET /v2/active-conf?country=CMR` |
| `INVALID_PHONE_NUMBER` | The number doesn't match the operator | Run it through `predict-provider` first |
| `INVALID_PROVIDER` / `INVALID_CURRENCY` | Wrong provider code, or a currency the provider doesn't take | Use `MTN_MOMO_CMR` or `ORANGE_CMR` with `XAF` |
| `DUPLICATE_METADATA_FIELD` | The same key twice in `metadata` | Use each key once |
| `PROVIDER_TEMPORARILY_UNAVAILABLE` | The operator is down | Try again later. `GET /v2/availability?country=CMR` shows the status |
| `UNKNOWN_ERROR` | Something broke inside PawaPay | Don't mark the payment failed yet. Check the status with the same ID first |

`DUPLICATE_IGNORED` is not an error. It means PawaPay already has a transaction with that ID, so it ignored the second request. Check the status of the first one.

## The payment failed

These arrive later, in the status check or a callback, with status `FAILED`. The request was fine, but the customer or operator said no. Show the customer a clear message and let them try again with a new ID.

| Code | What happened | Message for the customer |
| --- | --- | --- |
| `PAYMENT_NOT_APPROVED` | The customer didn't approve with their PIN in time | "Paiement non confirmé. Réessayez et validez avec votre code PIN." / "Payment not confirmed. Try again and approve it with your PIN." |
| `INSUFFICIENT_BALANCE` | Not enough money in the wallet | "Solde insuffisant. Rechargez votre compte et réessayez." / "Not enough balance. Top up and try again." |
| `PAYER_NOT_FOUND` | The number isn't on that operator | "Ce numéro n'est pas reconnu par l'opérateur choisi." / "This number isn't registered with the operator you chose." |
| `PAYER_LIMIT_REACHED` | The customer hit their wallet limit | "Limite de votre compte atteinte. Contactez votre opérateur." / "Your wallet limit is reached. Contact your operator." |
| `PAYMENT_IN_PROGRESS` | The customer has another payment waiting | "Un autre paiement est en cours. Patientez quelques minutes." / "Another payment is in progress. Wait a few minutes." |
| `UNSPECIFIED_FAILURE` | The operator failed without a reason | "Le paiement a échoué. Réessayez." / "The payment failed. Please try again." |

## Other problems

**The status stays `ACCEPTED` or `PROCESSING`.** In the sandbox this takes seconds unless you used a number that stays pending, such as `237653456129`. In production the customer has to answer the PIN prompt, which takes longer. Keep polling, and don't treat a pending payment as failed.

**`IN_RECONCILIATION`.** PawaPay is confirming the result with the operator. It resolves on its own. Keep polling.

**The status check returns `NOT_FOUND`.** PawaPay never received that ID. Either the first request failed before reaching PawaPay, or, for the hosted checkout, the customer hasn't pressed Pay yet.

**My browser JavaScript can't call the API.** Call PawaPay from your server, never from the browser or a mobile app. Code in the browser exposes your token to anyone who opens developer tools. Have your frontend call your own backend, and have the backend call PawaPay.

**My callback handler rejects every callback with a signature error.** On the shared CITS26 account, PawaPay signs callbacks for the forwarding service's address, so verification fails on your server. Turn signature verification off and reply `200`. See [tracking-transactions.md](tracking-transactions.md).

**The callback amount doesn't match what I sent.** Callbacks report amounts with decimals, such as `"1000.0000"` for `"1000"`. Compare them as numbers, not strings.

**Callbacks stopped for everyone.** Someone probably changed the **Callback URLs** or **API Security** settings in the dashboard. Tell the PawaPay team at the clinic desk, or email Joel.

**I can't find my transactions in the dashboard.** Every team shares the account. Search by your deposit ID, or by the `team` metadata tag. See [tracking-transactions.md](tracking-transactions.md).

**I never got the dashboard invite.** Check spam. Confirm you filled in the [registration form](https://docs.google.com/forms/d/e/1FAIpQLScC-s8bw7OKarp2PFg6xgOXXvGmgezpWpS5I69ZY54v3miOFg/viewform), then email Joel with the address you gave.

## FAQ

### Going live

**Can we take real money during the Summit?** The sandbox moves no real money. Going live needs a production account, which goes through PawaPay's onboarding. PawaPay's [going live guide](https://docs.pawapay.io/v2/docs/going_live) explains the steps, and the PawaPay clinic desk can tell you what that takes for your team.

**Do we need a registered company?** Not for the sandbox. For production, ask at the clinic desk.

**What are the fees, and when does money settle?** Ask at the clinic desk or at the fireside chat on 15 October. The answer depends on the account, so we don't publish it here.

### Building

**Do we need Claude to use this kit?** No. The [examples](examples/) run on plain Node, Python, PHP, or curl. The Claude skill speeds things up if you have it.

**Which countries work?** These docs focus on Cameroon (`XAF`, MTN and Orange). `GET /v2/active-conf` lists every country and operator enabled on the shared account.

**Can we get push callbacks instead of polling?** Yes. Your server needs a public HTTPS URL. On a laptop, a tunnel gives you one: `cloudflared tunnel --url http://localhost:3000` or `ngrok http 3000`. Every registered URL receives every team's callbacks, so filter by your `team` tag. [`examples/node/callback-server.mjs`](examples/node/callback-server.mjs) shows how. Add the URL to the [registration form](https://docs.google.com/forms/d/e/1FAIpQLScC-s8bw7OKarp2PFg6xgOXXvGmgezpWpS5I69ZY54v3miOFg/viewform). See [tracking-transactions.md](tracking-transactions.md).

**Can we build a USSD app, a WhatsApp bot, or a mobile app?** Yes. Any backend that can make HTTPS requests can call PawaPay. Keep the token on the server.

**What happens to the sandbox after the event?** The shared account exists for CITS26. Plan for it to close afterwards, and don't depend on it for anything long-term.
