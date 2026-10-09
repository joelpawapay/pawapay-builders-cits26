// Collect a mobile money payment (a deposit) on the PawaPay sandbox.
// Node 18+, no packages to install.
//
// Run from the examples/ folder:
//   node node/deposit.mjs [phoneNumber] [amount]
//   node node/deposit.mjs 237653456789 1000

import { randomUUID } from "node:crypto";
import { readFileSync, existsSync } from "node:fs";

// Load .env from the current folder into process.env.
if (existsSync(".env")) {
  for (const line of readFileSync(".env", "utf8").split("\n")) {
    const match = line.match(/^\s*([A-Z_]+)\s*=\s*(.*)\s*$/);
    if (match && !process.env[match[1]]) process.env[match[1]] = match[2];
  }
}

const TOKEN = process.env.PAWAPAY_API_TOKEN;
const BASE_URL = process.env.PAWAPAY_BASE_URL || "https://api.sandbox.pawapay.io";
const TEAM = process.env.PAWAPAY_TEAM || "team-unknown";

if (!TOKEN || TOKEN.startsWith("paste-")) {
  console.error("Set PAWAPAY_API_TOKEN in examples/.env first. See getting-started.md.");
  process.exit(1);
}

const phoneInput = process.argv[2] || "237653456789";
const amount = process.argv[3] || "1000";

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

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// 1. Clean up the phone number and find out which operator it belongs to.
const predicted = await pawapay("POST", "/v2/predict-provider", { phoneNumber: phoneInput });
console.log(`Phone ${predicted.phoneNumber} is on ${predicted.provider}`);

// 2. Create the deposit ID yourself. In a real app, save it to your database now.
const depositId = randomUUID();

// 3. Ask PawaPay to collect the money.
const initiated = await pawapay("POST", "/v2/deposits", {
  depositId,
  amount, // a string, never a number. XAF has no decimals.
  currency: "XAF",
  payer: {
    type: "MMO",
    accountDetails: { phoneNumber: predicted.phoneNumber, provider: predicted.provider },
  },
  customerMessage: "CITS26 test",
  metadata: [{ team: TEAM }],
});
console.log(`Deposit ${depositId}: ${initiated.status}`);
if (initiated.status !== "ACCEPTED") process.exit(1);

// 4. ACCEPTED is not paid. Poll until the deposit reaches COMPLETED or FAILED.
for (let attempt = 1; attempt <= 20; attempt++) {
  await sleep(3000);
  const check = await pawapay("GET", `/v2/deposits/${depositId}`);
  const status = check.status === "FOUND" ? check.data.status : check.status;
  console.log(`  check ${attempt}: ${status}`);

  if (status === "COMPLETED") {
    console.log("Payment received. Deliver the goods.");
    process.exit(0);
  }
  if (status === "FAILED") {
    const reason = check.data.failureReason;
    console.log(`Payment failed: ${reason?.failureCode} (${reason?.failureMessage})`);
    process.exit(1);
  }
}
console.log("Still pending after 60 seconds. Check again later with the deposit ID above.");
