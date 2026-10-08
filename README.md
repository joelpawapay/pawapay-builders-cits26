# pawaPay Builders: CITS26

<img src="assets/repo-qr.png" alt="QR code linking to this repository" width="140" align="right">

Take mobile money payments in your Bootcamp project. MTN MoMo and Orange Money, Cameroon, any language.

🇫🇷 **[Lire en français](README.fr.md)**

This kit is for teams at the **Cameroon International Tech Summit 2026** (CITS26), Palais des Congrès, Yaoundé. The National Innovation Bootcamp runs on 14 October and the Summit runs from 15 to 17 October. Teams are scored on deals closed during the Summit, so your product needs to take a payment.

pawaPay gives every team free access to a shared sandbox: a test copy of the payment system where no real money moves.

## Your first payment in 15 minutes

1. **Get access.** Email Joel at [joel.amoako@pawapay.co.uk](mailto:joel.amoako@pawapay.co.uk) with your team name and each member's email. Accept the invite from pawaPay.
2. **Create a token** in the [sandbox dashboard](https://dashboard.sandbox.pawapay.io) under **System configuration → API tokens**. Copy it. pawaPay shows it once.
3. **Run a payment:**

   ```bash
   git clone https://github.com/joelpawapay/pawapay-builders-cits26.git
   cd pawapay-builders-cits26/examples
   cp .env.example .env        # paste your token into .env
   node node/deposit.mjs       # or python3 python/deposit.py, or php php/deposit.php
   ```

4. **See `Payment received.`** You just collected 1000 XAF from a test MTN number.

Stuck on a step? [getting-started.md](getting-started.md) covers each one in detail.

## Pick your path

| You're building | Start with |
| --- | --- |
| A website, and you want the least code | Hosted checkout: pawaPay shows the payment form. [`examples/node/payment-page.mjs`](examples/node/payment-page.mjs) |
| An app, API, USSD service, or bot | The deposit API. [`examples/`](examples/) has Node, Python, PHP, and curl |
| A WordPress shop | The [WooCommerce plugin](plugin/) |
| Anything, with Claude as your pair programmer | The [Claude skill](skill/). It writes pawaPay code that works against the sandbox |
| Nothing yet, just exploring the API | The [Postman collection](examples/postman/) |

Never used a payment API? Read [how-payments-work.md](how-payments-work.md) first. It takes five minutes.

## What's in this repo

| Path | What it's for |
| --- | --- |
| [getting-started.md](getting-started.md) | Access, token, `.env`, and the Cameroon test numbers |
| [how-payments-work.md](how-payments-work.md) | How a mobile money payment moves, for first-time integrators |
| [examples/](examples/) | Runnable scripts and a Postman collection. No packages to install |
| [troubleshooting.md](troubleshooting.md) | Every error code with its fix, customer messages in French and English, and an FAQ |
| [tracking-transactions.md](tracking-transactions.md) | Finding your transactions on the shared account, and push callbacks |
| [demo-checklist.md](demo-checklist.md) | What to check before you present |
| [resources.md](resources.md) | Links, sessions, and contacts |
| [skill/](skill/) | Claude skill for pawaPay |
| [plugin/](plugin/) | WooCommerce payment gateway |

## pawaPay at the event

| When | Session |
| --- | --- |
| 14 Oct, 09:00 | Talk to the Bootcamp cohort |
| 14 Oct, 11:00 | Integration clinic. Bring a laptop and leave with a working sandbox payment |
| 15 Oct, from 12:00 | pawaPay clinic desk, open to anyone with an integration question |
| 15 Oct, 14:00 | Fireside chat on pawaPay infrastructure, main stage |
| 16 Oct, 09:00 | Developer workshop, 90 minutes. Bring a problem you're stuck on |

Times follow the draft programme. Check the printed programme at the venue.

To get the most from the clinic, accept your sandbox invite and create your token before 11:00 on the 14th.

## Five rules that save you an afternoon

1. `ACCEPTED` means pawaPay received the request. Wait for `COMPLETED` before you deliver anything.
2. Amounts are strings with no decimals in XAF: `"1000"`.
3. Phone numbers carry the country code and nothing else: `237653456789`.
4. Create the transaction ID (a UUIDv4) yourself and save it before you call pawaPay.
5. Call pawaPay from your server. A token in browser or mobile code is a token anyone can copy.

## Getting help

- **Sandbox access, tokens, callbacks**: email Joel at joel.amoako@pawapay.co.uk
- **At the venue**: Dave Evans (14 to 16 October) and the pawaPay Cameroon team at the clinic desk
- **An error code**: [troubleshooting.md](troubleshooting.md)

Good luck. Build something people pay for.
