# Tracking transactions on the shared sandbox

The dashboard and API responses contain transactions from every team on the shared account. You need a way to identify yours.

Four patterns work. Mix and match.

## Option A: tag every transaction with a participant ID (metadata)

pawaPay accepts arbitrary key-value metadata on a deposit. Stamp every request with a team identifier:

```json
{
  "depositId": "f4401bd2-1b8c-4017-9a8c-9a5c0c1e9d2a",
  "amount": "1000",
  "currency": "XAF",
  "payer": {
    "type": "MMO",
    "accountDetails": {
      "phoneNumber": "237653456789",
      "provider": "MTN_MOMO_CMR"
    }
  },
  "metadata": [
    { "team": "team-ndole" },
    { "participant": "jane@example.com", "isPII": true }
  ]
}
```

**Why pick this:** you can filter and search in the sandbox dashboard, and the tag survives across deposit IDs you might forget about.

**Caveats:** you have to set it on every request. Put the tag in config so you can't forget it. The [examples](examples/) read it from `PAWAPAY_TEAM` in `.env`.

The WooCommerce plugin doesn't add metadata out of the box. You'd add it via a small WP filter hook. If you're building from scratch, ask the skill to wire in the metadata block. See the [Deposits API reference](https://docs.pawapay.io/v2/api-reference/Deposits/initiate-deposit) for the schema.

## Option B: track your own transaction UUIDs

Every deposit, payout, refund, or remittance you create has a UUID (`depositId`, `payoutId`, etc.). Log them as you create them. Those are your records.

**Why pick this:** zero setup. The WooCommerce plugin already stores the pawaPay transaction ID against each order. If you're rolling your own, persist the ID in your DB the moment you generate it. The skill enforces this, because the same UUID is how pawaPay handles idempotency.

**Caveats:** lose your local log (database wipe, lost laptop), lose the link. Pair this with Option A for safety.

## Option C: have pawaPay forward callbacks to your URL (optional)

If you want status updates as push callbacks instead of polling, pawaPay can forward callbacks to a URL of your choice. Add your public URLs to the [registration form](https://docs.google.com/forms/d/e/1FAIpQLScC-s8bw7OKarp2PFg6xgOXXvGmgezpWpS5I69ZY54v3miOFg/viewform): one each for deposit, payout, and refund callbacks, whichever you need. If your URL changes after you register, email Joel at [joel.amoako@pawapay.co.uk](mailto:joel.amoako@pawapay.co.uk) with the new one.

**How it works on the shared account:** pawaPay sends every callback from the CITS26 account to every registered URL. Your server receives other teams' callbacks too. Reply `200` to all of them, then keep the ones tagged with your team (Option A) or whose ID you created (Option B). [`examples/node/callback-server.mjs`](examples/node/callback-server.mjs) does this.

**Why pick this:** status updates arrive as soon as a payment completes, with no polling loop.

**Caveats:** callbacks need a public HTTPS URL on your side. A deployed app has one. On a laptop, open a tunnel to your local server:

```bash
cloudflared tunnel --url http://localhost:3000   # or: ngrok http 3000
```

Tunnel URLs change each time you restart the tunnel, so send Joel the new one when it does. Your handler must reply `200` quickly, including for callbacks it ignores. pawaPay retries, so the same callback can arrive more than once. For a Bootcamp demo, polling is less hassle.

## Option D: poll for status (recommended default)

Hit the pawaPay status endpoint when you need to know the outcome.

```
GET https://api.sandbox.pawapay.io/v2/deposits/<depositId>
```

The WooCommerce plugin polls for you on the checkout page until the deposit reaches a terminal state. No extra config. The [examples](examples/) poll every 3 seconds. If you use Claude, ask the skill to wire up polling with backoff and reconciliation.

**Why pick this:** no callback URL, no public hostname, no firewall holes. Works in any stack.

**Caveats:** higher latency than callbacks. For a Bootcamp demo, that's fine.

## Useful links

- [pawaPay v2 docs: welcome](https://docs.pawapay.io/v2/docs/welcome)
- [Deposits API reference](https://docs.pawapay.io/v2/api-reference/Deposits/initiate-deposit)
- [Sandbox test numbers](https://docs.pawapay.io/v2/docs/test_numbers)
