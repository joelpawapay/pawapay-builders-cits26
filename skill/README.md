# pawapay-merchant-api-v2: Claude skill

A Claude skill: a self-contained bundle of reference docs and scripts. Load it into Claude and Claude can write production pawaPay integrations without you digging through API docs.

This is the same skill that built the WooCommerce plugin in this repo in about six prompts. Use it for anything.

🎥 **Demo**: [Loom walkthrough](https://www.loom.com/share/af99d1a8a13048a89220d21f1e001226)

## What's in here

| Path | What it is |
| --- | --- |
| `SKILL.md` | Top-level skill instructions Claude reads first. Covers the async state machine, signing, sandbox setup, and the decision tree to the right reference file |
| `references/` | Deep-dive endpoint docs: deposits, payouts, refunds, remittances, payment page, statements, toolkit, callbacks, errors, testing, providers, auth |
| `scripts/` | Reference implementations of RFC 9421 request signing (Node and Python) and callback signature verification (Python) |

## How to use it

The easiest path is **Claude Code** (the CLI). Drop the skill into your project or user skills directory. It becomes invokable inside any Claude Code session.

### Option 1: project-local (recommended for the Bootcamp)

From inside the project you're working on:

```bash
mkdir -p .claude/skills
cp -r /path/to/pawapay-builders/skill .claude/skills/pawapay-merchant-api-v2
```

Start Claude Code in that project. The skill auto-activates when you mention pawaPay, mobile money, MMO, MTN MoMo, M-Pesa, Wave, deposits, payouts, and other related terms. See the `description` field in `SKILL.md` for the full trigger list.

### Option 2: user-wide

For the skill available across every project on your machine:

```bash
mkdir -p ~/.claude/skills
cp -r /path/to/pawapay-builders/skill ~/.claude/skills/pawapay-merchant-api-v2
```

### Option 3: Claude.ai (web)

Open Claude.ai in Code mode, go to skills, upload this folder. The [Loom walkthrough](https://www.loom.com/share/af99d1a8a13048a89220d21f1e001226) shows the flow.

## What to ask Claude once the skill is loaded

Give Claude a concrete build task. Examples:

- *"Read PAWAPAY_API_TOKEN from .env and build a checkout page that collects XAF from MTN MoMo or Orange Money in Cameroon."*
- *"Build a Next.js API route that accepts a phone number and amount, validates the number via `predict-provider`, then initiates a sandbox deposit. Persist the depositId and poll for status."*
- *"Add a Wave redirect flow to my existing pawaPay deposit handler."*
- *"Write a Python callback handler that verifies pawaPay's RFC 9421 signature and is idempotent on retry."*
- *"Walk me through what needs to change in my code to handle the `ENQUEUED` state on payouts."*

Claude reads the right reference file(s) before generating code, and uses the scripts in `scripts/` as the source of truth for signing.

## Things to know

- The skill targets the **Merchant API v2**, not v1. It refuses to write v1 calls.
- The skill assumes you have a sandbox API token. See [`../getting-started.md`](../getting-started.md) for how to get one.
- Amounts are always **strings**, never floats. The skill enforces this. Let it.
- Every transaction needs a **UUIDv4 ID you generate** before the API call, for idempotency. The skill drills this in.
- **Callbacks on the shared CITS26 account:** the skill verifies callback signatures by default. On the shared account that check fails, because pawaPay signs callbacks for the forwarding service's address. Tell Claude "don't verify callback signatures, and filter callbacks by the `team` metadata tag". See [`../tracking-transactions.md`](../tracking-transactions.md).

## Reporting issues with the skill

Email Joel at [joel.amoako@pawapay.co.uk](mailto:joel.amoako@pawapay.co.uk) with the prompt and the wrong output. pawaPay will fix the skill.
