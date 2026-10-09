# Examples

Small scripts that take a real sandbox payment from start to finish. Each one runs with the language's standard tools, so you install nothing. Copy the code into your project once it works.

## Set up once

```bash
cd examples
cp .env.example .env
```

Open `.env` and paste your sandbox token. [getting-started.md](../getting-started.md) explains how to get one.

## Run

Run every command from the `examples/` folder.

| Example | Command | Needs |
| --- | --- | --- |
| Deposit, Node | `node node/deposit.mjs` | Node 18 or newer |
| Deposit, Python | `python3 python/deposit.py` | Python 3.8 or newer |
| Deposit, PHP | `php php/deposit.php` | PHP 7.4 or newer with curl |
| Deposit, curl | `bash curl/deposit.sh` | bash and curl |
| Hosted checkout, Node | `node node/payment-page.mjs` | Node 18 or newer |
| Callback receiver, Node | `node node/callback-server.mjs` | Node 18 or newer, plus a tunnel such as `cloudflared` |
| Postman | Import `postman/pawapay-cits26.postman_collection.json` | [Postman](https://www.postman.com/downloads/) |

The deposit scripts take an optional phone number and amount: `node node/deposit.mjs 237693456789 2500`. With no arguments they charge 1000 XAF to the MTN sandbox number.

A successful run looks like this:

```
Phone 237653456789 is on MTN_MOMO_CMR
Deposit 0c5f1d0e-3b7a-4b52-9a51-2f0f6f3a9d11: ACCEPTED
  check 1: PROCESSING
  check 2: COMPLETED
Payment received. Deliver the goods.
```

## What each deposit script does

1. Sends the phone number to `predict-provider`, which cleans it up and names the operator.
2. Creates a UUIDv4 deposit ID.
3. Sends the deposit to pawaPay with a `team` tag in the metadata.
4. Checks the status every 3 seconds until the deposit is `COMPLETED` or `FAILED`.

## API reference for each call

| Script step | pawaPay reference |
| --- | --- |
| Predict the operator | [Predict provider](https://docs.pawapay.io/v2/api-reference/toolkit/predict-provider) |
| Start a deposit | [Initiate deposit](https://docs.pawapay.io/v2/api-reference/deposits/initiate-deposit) |
| Check the status | [Check deposit status](https://docs.pawapay.io/v2/api-reference/deposits/check-deposit-status) |
| Hosted checkout | [Deposit via payment page](https://docs.pawapay.io/v2/api-reference/payment-page/deposit-via-payment-page) |
| Receive a callback | [Deposit callback](https://docs.pawapay.io/v2/api-reference/deposits/deposit-callback) |
| Send money out | [Initiate payout](https://docs.pawapay.io/v2/api-reference/payouts/initiate-payout) |
| Limits and operators on the account | [Active configuration](https://docs.pawapay.io/v2/api-reference/toolkit/active-configuration) |

## Deposit or hosted checkout?

| | Deposit API | Hosted checkout (payment page) |
| --- | --- | --- |
| Who builds the payment form | You | pawaPay |
| Customer leaves your site | No | Yes, then returns to your `returnUrl` |
| Code to write | More | Less |
| Good for | Apps, USSD, bots, custom checkouts | Websites and quick demos |

With the hosted checkout, pawaPay sends the customer back to your `returnUrl`. Anyone can open that URL, so check the deposit status with pawaPay before you mark the order paid. `payment-page.mjs check <depositId>` shows how.

## Back from the hosted checkout

After you pay on the hosted checkout, pawaPay sends you back to this section, the default `returnUrl` in the examples. Your payment went through pawaPay, but a return visit proves nothing. Confirm it with the status check:

```bash
node node/payment-page.mjs check <depositId>
```

In your own app, set `RETURN_URL` in `.env` to a page on your site, and run that same status check before you mark the order paid.

## Postman

Two collections, for two jobs:

- **This repo's collection** (`postman/pawapay-cits26.postman_collection.json`) is set up for Cameroon: XAF, MTN and Orange, the `team` tag, and fresh IDs for every request. Start here.
- **[pawaPay's official collection](https://app.getpostman.com/run-collection/25129489-56cbaf62-56c2-4734-bf1f-f61d369cc9e3?action=collection%2Ffork&source=rip_markdown&collection-url=entityId%3D25129489-56cbaf62-56c2-4734-bf1f-f61d369cc9e3%26entityType%3Dcollection%26workspaceId%3D8c3e7775-3da5-4bab-8a8c-ffb331ccfe27)** covers every endpoint in the API. Follow the [Postman guide](https://docs.pawapay.io/v2/docs/postman) to set it up, using the variables `apiToken` and `baseUrl`. Skip the guide's step that sets callback URLs: on the shared account those are already set for every team.

To use this repo's collection:

1. Import `postman/pawapay-cits26.postman_collection.json`.
2. Open the collection's **Variables** tab. Set `token` to your sandbox token and `team` to your team name.
3. Run the requests in order. Each Initiate request creates a new ID, and the Check status request after it reuses that ID.

## Try the failure cases

Pass a different test number to make the sandbox fail on purpose:

```bash
node node/deposit.mjs 237693456049   # Orange: FAILED, INSUFFICIENT_BALANCE
node node/deposit.mjs 237653456039   # MTN: FAILED, PAYMENT_NOT_APPROVED
```

The full Cameroon list is in [getting-started.md](../getting-started.md#cameroon-sandbox-numbers).
