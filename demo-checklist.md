# Demo checklist

Run through this before you present. A live payment on screen is the strongest part of any demo, and conference Wi-Fi is where it breaks.

## The day before

- [ ] Run one full payment from your app's UI, not from a script.
- [ ] Run one failed payment too (`237693456049` gives Orange `INSUFFICIENT_BALANCE`). Show that your app handles it.
- [ ] Your app waits for `COMPLETED` before it shows "paid". `ACCEPTED` is not enough.
- [ ] Your token lives in `.env` or your host's settings, not in your code or your GitHub repo.
- [ ] Your deployed app has the token too. Check the environment variables on Vercel, Render, Railway, or wherever it runs.
- [ ] Every transaction carries your `team` metadata tag, so the pawaPay team can find your payments.

## One hour before

- [ ] Open the sandbox dashboard and log in, in case you need to show a transaction.
- [ ] Write down two test numbers: `237653456789` (MTN, succeeds) and `237693456789` (Orange, succeeds).
- [ ] Test on the venue Wi-Fi. If it's slow, use a phone hotspot.
- [ ] Record a 30-second screen capture of a working payment as a backup.

## During the demo

- [ ] Say what problem you solve and who pays, in one sentence.
- [ ] Take the payment live. Narrate it: "the customer enters their number, approves on their phone, and we confirm."
- [ ] Mention that in production the customer approves with their MTN MoMo or Orange Money PIN. The sandbox skips that step.
- [ ] Show what happens when a payment fails.

## If something breaks

- `AUTHENTICATION_ERROR`: the token is missing or wrong in the environment you're running.
- Stuck on pending: check you used a success number, not `...129`.
- Anything else: [troubleshooting.md](troubleshooting.md), or find the pawaPay team at the clinic desk.
