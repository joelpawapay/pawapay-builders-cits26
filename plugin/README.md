# pawaPay WooCommerce Plugin

A WooCommerce payment gateway for pawaPay. Mobile money deposits across every pawaPay-supported country and provider.

> **Optional.** Use this if you want a WordPress and WooCommerce starting point. For anything else (Next.js, Flutter, mobile app, custom backend), skip this folder and use the [Claude skill](../skill/README.md).

## What it does

- Adds **Mobile Money** as a payment method at WooCommerce checkout
- Supports **Blocks** (the new WooCommerce checkout) and the **classic shortcode** checkout
- Predicts the provider from the customer's phone number. No carrier picker for supported numbers
- Handles **on-site deposits** via the pawaPay v2 Deposits API, with polling for status
- Handles the **Wave redirect flow** where applicable
- Wires up **refunds** from the WooCommerce admin
- Supports **RFC 9421 request signing** (optional, signing key configured in admin)
- Provides an admin settings page for token, environment (sandbox or production), and signing key

## Prerequisites

- WordPress 6.4+ (tested on 6.9)
- WooCommerce 8.0+
- A pawaPay sandbox account and API token. See [../getting-started.md](../getting-started.md)

## Install

1. Download `woocommerce-pawapay.zip` from this directory.
2. In the WordPress admin, open **Plugins → Add New → Upload Plugin**. Pick the `.zip`, install, activate.
3. Go to **WooCommerce → Settings → Payments**. **Mobile Money (pawaPay)** appears in the list.
4. Click **Manage**, then:
   - Paste your sandbox API token (see [getting-started.md](../getting-started.md) for how to generate one)
   - Set environment to **Sandbox**
   - Optional: paste a signing key for signed requests
   - **Callback URL**: leave blank. The plugin polls. If you need push callbacks, see [../tracking-transactions.md](../tracking-transactions.md).
5. Save. Add a product, go to checkout, push a sandbox deposit through.

## Configuration reference

| Setting | What to put |
| --- | --- |
| API token | Your sandbox token from the dashboard |
| Environment | `Sandbox` while building. `Production` is for live merchants |
| Signing key | Optional. Set this for HTTP signatures on requests |
| Callback URL | Leave blank at the Bootcamp. The plugin polls. For push callbacks, see the tracking doc |

## Testing in sandbox

In sandbox, pawaPay simulates the provider flow. No real mobile-money account needed. Set the store currency to XAF and use the Cameroon sandbox numbers in [../getting-started.md](../getting-started.md). The plugin will show status transitions (pending → completed or failed) in the WooCommerce order view.

## Troubleshooting

- **"Mobile Money" doesn't appear at checkout.** Check the gateway is enabled in WC settings and that your store country matches a pawaPay-supported country.
- **Token rejected.** Confirm you're using a sandbox token while the gateway is set to Sandbox. Production tokens won't work in sandbox and vice versa.
- **Stuck on "pending".** pawaPay deposits resolve asynchronously and the plugin polls. If you configured a callback URL that isn't reachable, switch to polling-only and try again. See [../tracking-transactions.md](../tracking-transactions.md).
- **Anything else.** Bring it to the pawaPay clinic desk, email Joel, or check the [pawaPay docs](https://docs.pawapay.io/v2/docs/welcome).

## Plugin bundle contents

The `.zip` contains:

- `woocommerce-pawapay.php`: main plugin file
- `includes/`: the gateway, REST client, Blocks support, signing, logger
- `readme.txt`: WordPress.org-style plugin readme
- `docker/`: optional `docker-compose` setup for a local WP and WooCommerce environment with the plugin pre-mounted (see `docker/README.md` inside)
