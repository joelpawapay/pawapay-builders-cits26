# pawaPay Builders: CITS26

The starter kit for pawaPay at the **Cameroon International Tech Summit 2026** (CITS26), Palais des Congrès, Yaoundé.

The National Innovation Bootcamp runs on 14 October and the Summit runs from 15 to 17 October. Bootcamp teams are scored on deals they close during the Summit, so your product needs to take a payment. This repo gets you from zero to a working mobile money payment on the pawaPay sandbox. MTN MoMo and Orange Money in Cameroon are both on it, and you can use any language or framework.

## Start here

1. [getting-started.md](getting-started.md): get sandbox access, create an API token, and put it in a `.env` file.
2. New to payment APIs? Read [how-payments-work.md](how-payments-work.md) first. It takes five minutes.
3. Pick a path:
   - Build in any stack: load the [Claude skill](skill/) into Claude and ask it to write your integration.
   - Run a WordPress shop: install the [WooCommerce plugin](plugin/) and take payments at checkout.
4. Tag your transactions so you can find them on the shared account: [tracking-transactions.md](tracking-transactions.md).

Every link lives in [resources.md](resources.md).

> **Demo**: [Loom walkthrough](https://www.loom.com/share/af99d1a8a13048a89220d21f1e001226). The WooCommerce plugin in this repo took about six prompts to build with the skill.

## What's in this repo

| Path | What it is |
| --- | --- |
| [getting-started.md](getting-started.md) | Sandbox access, API token, `.env` setup, first test payment |
| [how-payments-work.md](how-payments-work.md) | How a mobile money payment moves through pawaPay, for first-time integrators |
| [tracking-transactions.md](tracking-transactions.md) | Four ways to find your transactions on the shared sandbox account |
| [resources.md](resources.md) | Links, pawaPay sessions at the event, and contacts |
| [skill/](skill/) | Claude skill bundle. Load it into Claude Code or Claude.ai and Claude writes pawaPay code that works against the sandbox |
| [plugin/](plugin/) | WooCommerce payment gateway `.zip`. Optional, for teams selling through WordPress |

## pawaPay at the event

| When | Session |
| --- | --- |
| 14 Oct, 09:00 | Talk to the Bootcamp cohort |
| 14 Oct, 11:00 | Integration clinic. Bring a laptop and leave with a working sandbox |
| 15 Oct, from 12:00 | pawaPay clinic desk, open to anyone with an integration question |
| 15 Oct, 14:00 | Fireside chat on pawaPay infrastructure, main stage |
| 16 Oct, 09:00 | Developer workshop, 90 minutes. Bring a problem |

Times follow the draft programme. Check the printed programme at the venue for changes.

## Key links

- pawaPay docs: https://docs.pawapay.io/v2/docs/welcome
- Sandbox dashboard: https://dashboard.sandbox.pawapay.io
- API token guide: https://docs.pawapay.io/dashboard/other/system_conf/api_tokens

> Polling works out of the box. If you want pawaPay to push status callbacks to your server, email Joel and pawaPay will set them up. See [tracking-transactions.md](tracking-transactions.md).

## Getting help

- Sandbox access and API tokens: email Joel at joel.amoako@pawapay.co.uk
- At the venue: Dave Evans (14 to 16 October) and the pawaPay Cameroon team
- Everything else: [resources.md](resources.md)

Good luck. Build something people pay for.
