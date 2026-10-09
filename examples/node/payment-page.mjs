// Create a PawaPay hosted checkout link. PawaPay shows the payment form,
// so you build no payment UI. Open the link, pay, and PawaPay sends the
// customer back to RETURN_URL.
// Node 18+, no packages to install.
//
// Run from the examples/ folder:
//   node node/payment-page.mjs [amount]
// Then check the result:
//   node node/payment-page.mjs check <depositId>

import { randomUUID } from "node:crypto";
import { readFileSync, existsSync } from "node:fs";

if (existsSync(".env")) {
  for (const line of readFileSync(".env", "utf8").split("\n")) {
    const match = line.match(/^\s*([A-Z_]+)\s*=\s*(.*)\s*$/);
    if (match && !process.env[match[1]]) process.env[match[1]] = match[2];
  }
}

const TOKEN = process.env.PAWAPAY_API_TOKEN;
const BASE_URL = process.env.PAWAPAY_BASE_URL || "https://api.sandbox.pawapay.io";
const TEAM = process.env.PAWAPAY_TEAM || "team-unknown";
const RETURN_URL = process.env.RETURN_URL || "https://github.com/joelpawapay/pawapay-builders-cits26/blob/main/examples/README.md#back-from-the-hosted-checkout";

if (!TOKEN || TOKEN.startsWith("paste-")) {
  console.error("Set PAWAPAY_API_TOKEN in examples/.env first. See getting-started.md.");
  process.exit(1);
}

function stop(message) {
  console.error(`PawaPay said: ${message}`);
  if (/AUTHENTICATION|AUTHORISATION/.test(message)) {
    console.error("Check PAWAPAY_API_TOKEN in examples/.env. It must be a sandbox token.");
  }
  process.exit(1);
}

async function pawapay(method, path, body) {
  const res = await fetch(BASE_URL + path, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  }).catch((error) => stop(`network error: ${error.message}`));
  const data = await res.json().catch(() => ({}));
  if (data.failureReason) {
    stop(`${data.failureReason.failureCode}: ${data.failureReason.failureMessage}`);
  }
  if (!res.ok) stop(`HTTP ${res.status}: ${JSON.stringify(data)}`);
  return data;
}

if (process.argv[2] === "check") {
  // Always confirm the result with PawaPay. Anyone can visit your return URL.
  const check = await pawapay("GET", `/v2/deposits/${process.argv[3]}`);
  if (check.status === "NOT_FOUND") {
    console.log("No payment yet. The customer has not pressed Pay, or the link expired.");
  } else {
    console.log(`Status: ${check.data.status}`);
  }
  process.exit(0);
}

const depositId = randomUUID();
const page = await pawapay("POST", "/v2/paymentpage", {
  depositId,
  returnUrl: RETURN_URL,
  amountDetails: { amount: process.argv[2] || "1000", currency: "XAF" },
  country: "CMR", // required when you set amountDetails
  language: "FR", // EN or FR
  reason: "CITS26 test order",
  metadata: [{ team: TEAM }],
});

console.log(`Deposit ID: ${depositId}`);
console.log(`Open this link within 15 minutes: ${page.redirectUrl}`);
console.log(`Then run: node node/payment-page.mjs check ${depositId}`);
