// Receive pawaPay callbacks (push status updates) on your own server.
// Node 18+, no packages to install.
//
// On the shared CITS26 account, pawaPay forwards every team's callbacks to
// every registered URL. This server keeps the ones tagged with your team
// and ignores the rest. It doesn't verify signatures: on the shared account
// pawaPay signs callbacks for the forwarding service's address, so a
// signature check here would always fail.
//
// Run from the examples/ folder:
//   node node/callback-server.mjs
// Then make it public in a second terminal:
//   cloudflared tunnel --url http://localhost:3000

import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";

if (existsSync(".env")) {
  for (const line of readFileSync(".env", "utf8").split("\n")) {
    const match = line.match(/^\s*([A-Z_]+)\s*=\s*(.*)\s*$/);
    if (match && !process.env[match[1]]) process.env[match[1]] = match[2];
  }
}

const TEAM = process.env.PAWAPAY_TEAM || "team-unknown";
const PORT = Number(process.env.PORT || 3000);
const seen = new Set(); // pawaPay retries, so the same callback can arrive twice

createServer((req, res) => {
  if (req.method !== "POST") {
    res.writeHead(200).end("callback server up");
    return;
  }

  let raw = "";
  req.on("data", (chunk) => (raw += chunk));
  req.on("end", () => {
    // Reply 200 straight away, even for callbacks you ignore.
    // Anything else makes pawaPay retry.
    res.writeHead(200).end("ok");

    let callback;
    try {
      callback = JSON.parse(raw);
    } catch {
      console.log("Ignored a body that isn't JSON");
      return;
    }

    if (callback.metadata?.team !== TEAM) return; // another team's transaction

    const id = callback.depositId || callback.payoutId || callback.refundId;
    const key = `${id}:${callback.status}`;
    if (seen.has(key)) return;
    seen.add(key);

    console.log(`${req.url} ${id} is ${callback.status}`);
    if (callback.status === "FAILED") {
      console.log(`  reason: ${callback.failureReason?.failureCode}`);
    }
    // In your app: look up the order by this ID in your database and update it.
  });
}).listen(PORT, () => {
  console.log(`Listening on http://localhost:${PORT} for ${TEAM} callbacks`);
});
