# How a mobile money payment works

Read this if you've never connected an app to a payment API. It explains what happens between "customer taps Pay" and "money arrives", and where pawaPay sits in that flow.

## The three parties

- Your app: the shop, booking tool, or service your team builds.
- pawaPay: one API that connects your app to the mobile money operators.
- The operator: MTN MoMo or Orange Money in Cameroon. The customer's money sits in a wallet the operator runs.

You write code against one API. pawaPay talks to each operator for you, so adding Orange Money next to MTN MoMo needs no extra integration.

## Collecting money: a deposit

pawaPay calls money coming in from a customer a deposit. A deposit runs in five steps:

1. Your app creates a unique ID for the payment (a UUIDv4) and saves it.
2. Your app sends pawaPay the ID, the amount, the currency (`XAF`), the customer's phone number, and the operator.
3. pawaPay replies `ACCEPTED`. No money has moved yet.
4. The operator sends a prompt to the customer's phone. The customer enters their PIN to approve.
5. The deposit ends as `COMPLETED` or `FAILED`. Your app learns the result by asking pawaPay (polling) or by receiving a callback.

Step 3 trips up most first integrations. `ACCEPTED` means pawaPay received the request. Wait for `COMPLETED` before you deliver the goods.

In the sandbox, step 4 is skipped. No phone rings, and the deposit completes in a few seconds.

## Sending money: a payout

A payout runs the same flow in reverse: your app sends money from your pawaPay balance to a customer's wallet. Use it for refunds, seller earnings, prizes, or cash-back. A payout can sit in `ENQUEUED` while the operator is slow, then completes when the operator recovers.

A refund returns all or part of a completed deposit to the customer who paid.

## The rules that matter

- Make your own ID first, and save it before you call pawaPay. If your request times out, you can ask pawaPay for that ID's status. Sending the same ID twice returns `DUPLICATE_IGNORED`, so a retry never charges a customer twice.
- Send amounts as strings. `"1000"`, not `1000` or `1000.0`. XAF has no decimal places.
- Write phone numbers with the country code and nothing else. `237653456789`. pawaPay's `predict-provider` endpoint cleans up whatever the customer typed and tells you which operator the number belongs to.
- Handle failure. Customers cancel, run out of balance, or ignore the prompt. Show them a clear message and let them try again.

## Where to go next

- [getting-started.md](getting-started.md) to make your first sandbox deposit
- [pawaPay docs: deposits](https://docs.pawapay.io/v2/docs/deposits) for the full flow
- The [Claude skill](skill/README.md) to write the code with you
