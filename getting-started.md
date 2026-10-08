# Getting started on the shared sandbox

pawaPay runs one shared sandbox account for every team at CITS26. Joel adds you as a user, you log in to the dashboard, and you create your own API token. The sandbox moves no real money, and you don't need a registered company to use it.

## 1. Get added to the account

Email Joel at [joel.amoako@pawapay.co.uk](mailto:joel.amoako@pawapay.co.uk) with:

- Your team name
- The email address of each team member who needs dashboard access

Joel invites each address as a user on the shared sandbox account. pawaPay sends each person an invite email. Accept it and set a password.

> The account lives on **[dashboard.sandbox.pawapay.io](https://dashboard.sandbox.pawapay.io)**, not the production dashboard. You can't sign up yourself. The invite is the only way in.

## 2. Create an API token

Follow the official guide: **[pawaPay docs: API tokens](https://docs.pawapay.io/dashboard/other/system_conf/api_tokens)**

The short version:

1. Open **System configuration → API tokens** in the sandbox dashboard.
2. Click **Create token** and name it after your team (e.g. `team-<your-team-name>`).
3. Copy the token now. pawaPay shows it once.

Each team creates its own token. pawaPay can then revoke one team's token without breaking anyone else's build.

## 3. Put the token in a `.env` file

Keep the token out of your code. Create a file called `.env` in the root of your project:

```bash
PAWAPAY_API_TOKEN=paste-your-token-here
PAWAPAY_BASE_URL=https://api.sandbox.pawapay.io
```

Then add `.env` to `.gitignore` so the token never reaches GitHub:

```bash
echo ".env" >> .gitignore
```

Your code reads both values from the environment and sends the token as `Authorization: Bearer <token>` on every API call. The Claude skill follows this pattern when it writes code for you.

## 4. Make a test payment

Pick your build path:

- **Any stack**: load the [Claude skill](skill/README.md) and ask it for a deposit flow. A good first prompt: *"Read my token from .env and write a script that collects 1000 XAF from 237653456789 on MTN_MOMO_CMR in the pawaPay sandbox, then polls until the deposit completes."*
- **WooCommerce**: follow [plugin/README.md](plugin/README.md). Paste the token into the gateway settings and set the environment to **Sandbox**.

Use these sandbox numbers for Cameroon. They complete without a real phone:

| Provider | Phone number | Result |
| --- | --- | --- |
| `MTN_MOMO_CMR` | `237653456789` | COMPLETED |
| `ORANGE_CMR` | `237693456789` | COMPLETED |

The [pawaPay test numbers page](https://docs.pawapay.io/v2/docs/test_numbers) lists numbers that trigger each failure, such as `INSUFFICIENT_BALANCE` or `PAYMENT_NOT_APPROVED`. Test those too. Your customers will hit them.

Then read [tracking-transactions.md](tracking-transactions.md) to learn how to find your own transactions on the shared account.

## Common gotchas

- You can see every team's transactions in the dashboard. It's a shared account. Use the patterns in [tracking-transactions.md](tracking-transactions.md) to find yours.
- XAF has no decimals. Send `"1000"`, not `"1000.00"`. Amounts go in as strings, never numbers.
- Phone numbers need the country code. `237653456789`, not `+237 6 53 45 67 89` or `653456789`.
- Sandbox tokens don't work in production, and the reverse is also true.
- Lost your token? Create a new one and revoke the old one in the dashboard. pawaPay can't recover the original.
- Want to take real money? The sandbox can't. Talk to the pawaPay team at the clinic desk about going live.
