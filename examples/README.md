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
