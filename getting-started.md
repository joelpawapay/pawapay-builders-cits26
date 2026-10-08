# Getting started on the shared sandbox

pawaPay runs one shared sandbox account for every team at CITS26. Joel adds you as a user, you log in to the dashboard, and you create your own API token. The sandbox moves no real money, and you don't need a registered company to use it.

Plan on 15 minutes, most of it waiting for the invite email.

## 1. Get added to the account

Email Joel at [joel.amoako@pawapay.co.uk](mailto:joel.amoako@pawapay.co.uk) with:

- Your team name
- The email address of each team member who needs dashboard access

Joel invites each address as a user on the shared sandbox account. pawaPay sends each person an invite email. Accept it and set a password. Check your spam folder if it hasn't arrived after a few minutes.

> The account lives on **[dashboard.sandbox.pawapay.io](https://dashboard.sandbox.pawapay.io)**, not the production dashboard. You can't sign up yourself. The invite is the only way in.

## 2. Create an API token

Follow the official guide: [pawaPay docs: API tokens](https://docs.pawapay.io/dashboard/other/system_conf/api_tokens)

The short version:

1. Open **System configuration → API tokens** in the sandbox dashboard.
2. Click **Create token** and name it after your team (e.g. `team-<your-team-name>`).
3. Copy the token now. pawaPay shows it once.

One person per team creates the token and shares it with teammates over a private channel. pawaPay can then revoke one team's token without breaking anyone else's build.

## 3. Put the token in a `.env` file

Keep the token out of your code. Create a file called `.env` in the root of your project:

```bash
PAWAPAY_API_TOKEN=paste-your-token-here
PAWAPAY_BASE_URL=https://api.sandbox.pawapay.io
PAWAPAY_TEAM=team-your-team-name
```

To run this repo's examples, copy `examples/.env.example` to `examples/.env` and fill it in the same way.

Add `.env` to `.gitignore` so the token never reaches GitHub:

```bash
echo ".env" >> .gitignore
```

Your code reads these values from the environment and sends the token as `Authorization: Bearer <token>` on every API call.

## 4. Make a test payment

The fastest check that everything works:

```bash
git clone https://github.com/joelpawapay/pawapay-builders-cits26.git
cd pawapay-builders-cits26/examples
cp .env.example .env      # then paste your token into .env
node node/deposit.mjs     # or: python3 python/deposit.py, php php/deposit.php
```

You should see `Payment received.` within a few seconds. [examples/README.md](examples/README.md) covers every language, the hosted checkout, and the Postman collection.

Then build your own:

- **Any stack**: copy the example code into your app, or load the [Claude skill](skill/README.md) and ask it for the flow you need.
- **WooCommerce**: follow [plugin/README.md](plugin/README.md). Paste the token into the gateway settings and set the environment to **Sandbox**.

## Cameroon sandbox numbers

In the sandbox, the phone number decides the result. No real phone rings.

| Result | MTN (`MTN_MOMO_CMR`) | Orange (`ORANGE_CMR`) |
| --- | --- | --- |
| Deposit `COMPLETED` | `237653456789` | `237693456789` |
| Deposit `FAILED`: `PAYER_LIMIT_REACHED` | `237653456019` | `237693456019` |
| Deposit `FAILED`: `PAYER_NOT_FOUND` | `237653456029` | `237693456029` |
| Deposit `FAILED`: `PAYMENT_NOT_APPROVED` | `237653456039` | `237693456039` |
| Deposit `FAILED`: `INSUFFICIENT_BALANCE` | none | `237693456049` |
| Deposit `FAILED`: `UNSPECIFIED_FAILURE` | `237653456069` | `237693456069` |
| Stays pending (`SUBMITTED`) | `237653456129` | `237693456129` |
| Payout `COMPLETED` | `237653456789` | `237693456789` |
| Payout `FAILED`: `RECIPIENT_NOT_FOUND` | `237653456089` | none |
| Payout `FAILED`: `WALLET_LIMIT_REACHED` | none | `237693456099` |
| Payout `FAILED`: `UNSPECIFIED_FAILURE` | `237653456119` | `237693456119` |

Source: [pawaPay test numbers](https://docs.pawapay.io/v2/docs/test_numbers). Test the failures too. Real customers cancel, run out of balance, and ignore the PIN prompt.

Next, read [tracking-transactions.md](tracking-transactions.md) to find your own transactions on the shared account. If something breaks, see [troubleshooting.md](troubleshooting.md).

## Common gotchas

- You can see every team's transactions in the dashboard. It's a shared account. Tag yours with your team name (the examples do this).
- XAF has no decimals. Send `"1000"`, not `"1000.00"`. Amounts go in as strings, never numbers.
- Phone numbers need the country code: `237653456789`, not `+237 6 53 45 67 89` or `653456789`. The `predict-provider` endpoint fixes this for you.
- Sandbox tokens don't work in production, and the reverse is also true.
- Lost your token? Create a new one and revoke the old one in the dashboard. pawaPay can't recover the original.
- Want to take real money? The sandbox can't. See the FAQ in [troubleshooting.md](troubleshooting.md#going-live).
