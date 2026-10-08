// scripts/sign_request.js
// RFC 9421 message signature for pawaPay Merchant API v2.
// Default: ECDSA P-256 with SHA-256 over signature base, SHA-512 for the Content-Digest.
// Standard library only — no external deps.
//
// Usage:
//   import { signRequest } from "./sign_request.js";
//   const headers = signRequest({
//     method: "POST",
//     authority: "api.sandbox.pawapay.io",
//     path: "/v2/deposits",
//     body: Buffer.from(JSON.stringify(payload)),
//     privateKeyPem: process.env.PAWAPAY_PRIVATE_KEY,   // PEM string (P-256)
//     keyId: process.env.PAWAPAY_KEY_ID,
//     // optional:
//     algorithm: "ecdsa-p256-sha256",
//     digestAlgorithm: "sha-512",                      // "sha-512" | "sha-256"
//     lifetimeSeconds: 60,
//   });
//   // headers now contains: Content-Digest, Signature-Date, Signature, Signature-Input,
//   //                       Accept-Signature, Accept-Digest.
//   // Send these alongside Authorization + Content-Type with the same body bytes.

import { createHash, createSign, createPrivateKey } from "node:crypto";

const ACCEPT_SIGNATURE = "rsa-pss-sha512,ecdsa-p256-sha256,rsa-v1_5-sha256,ecdsa-p384-sha384";
const ACCEPT_DIGEST = "sha-256,sha-512";

/**
 * Sign a request and return the set of headers to attach.
 * NOTE: pawaPay expects you to send the EXACT bytes you signed. Serialise once, sign
 * those bytes, send those bytes. Don't re-serialise.
 */
export function signRequest({
  method,
  authority,
  path,
  body, // Buffer | Uint8Array — the exact bytes you will send
  privateKeyPem,
  keyId,
  algorithm = "ecdsa-p256-sha256",
  digestAlgorithm = "sha-512",
  lifetimeSeconds = 60,
  contentType = "application/json; charset=UTF-8",
}) {
  if (!Buffer.isBuffer(body) && !(body instanceof Uint8Array)) {
    throw new TypeError("body must be a Buffer or Uint8Array");
  }
  // 1. Content-Digest
  const digestNode = digestAlgorithm === "sha-256" ? "sha256" : "sha512";
  const digestB64 = createHash(digestNode).update(body).digest("base64");
  const contentDigest = `${digestAlgorithm}=:${digestB64}:`;

  // 2. Timestamps
  const created = Math.floor(Date.now() / 1000);
  const expires = created + lifetimeSeconds;
  const signatureDate = new Date().toISOString(); // e.g. 2024-05-02T15:36:45.058Z

  // 3. Build the covered components list and signature-input parameters
  const components = [
    `"@method": ${method.toUpperCase()}`,
    `"@authority": ${authority}`,
    `"@path": ${path}`,
    `"signature-date": ${signatureDate}`,
    `"content-digest": ${contentDigest}`,
    `"content-type": ${contentType}`,
  ];
  const coveredList = `("@method" "@authority" "@path" "signature-date" "content-digest" "content-type")`;
  const sigParams = `${coveredList};alg="${algorithm}";keyid="${keyId}";created=${created};expires=${expires}`;

  // 4. Signature base
  const signatureBase = [
    ...components,
    `"@signature-params": ${sigParams}`,
  ].join("\n");

  // 5. Sign with the chosen algorithm
  const signatureB64 = signWithAlgorithm(signatureBase, privateKeyPem, algorithm);

  // 6. Assemble headers
  return {
    "Content-Digest": contentDigest,
    "Signature-Date": signatureDate,
    "Signature": `sig-pp=:${signatureB64}:`,
    "Signature-Input": `sig-pp=${sigParams}`,
    "Accept-Signature": ACCEPT_SIGNATURE,
    "Accept-Digest": ACCEPT_DIGEST,
  };
}

function signWithAlgorithm(signatureBase, privateKeyPem, algorithm) {
  const priv = createPrivateKey(privateKeyPem);
  switch (algorithm) {
    case "ecdsa-p256-sha256": {
      const signer = createSign("sha256");
      signer.update(signatureBase);
      // ECDSA in Node produces DER-encoded signatures by default. RFC 9421 expects
      // the raw r||s concatenated form for ecdsa-p256-sha256. Use dsaEncoding: 'ieee-p1363'.
      const sigBuf = signer.sign({ key: priv, dsaEncoding: "ieee-p1363" });
      return sigBuf.toString("base64");
    }
    case "ecdsa-p384-sha384": {
      const signer = createSign("sha384");
      signer.update(signatureBase);
      const sigBuf = signer.sign({ key: priv, dsaEncoding: "ieee-p1363" });
      return sigBuf.toString("base64");
    }
    case "rsa-pss-sha512": {
      const signer = createSign("sha512");
      signer.update(signatureBase);
      const sigBuf = signer.sign({
        key: priv,
        padding: 6, // RSA_PKCS1_PSS_PADDING
        saltLength: 64,
      });
      return sigBuf.toString("base64");
    }
    case "rsa-v1_5-sha256": {
      const signer = createSign("sha256");
      signer.update(signatureBase);
      const sigBuf = signer.sign(priv); // default PKCS1 v1.5 for RSA
      return sigBuf.toString("base64");
    }
    default:
      throw new Error(`Unsupported algorithm: ${algorithm}`);
  }
}

// CLI smoke-test:
//   node sign_request.js
// Generates a key, signs a fake body, prints headers.
if (import.meta.url === `file://${process.argv[1]}`) {
  const { generateKeyPairSync } = await import("node:crypto");
  const { privateKey, publicKey } = generateKeyPairSync("ec", { namedCurve: "prime256v1" });
  const privPem = privateKey.export({ format: "pem", type: "pkcs8" });
  const body = Buffer.from(JSON.stringify({
    depositId: "f4401bd2-1568-4140-bf2d-eb77d2b2b639",
    amount: "15", currency: "ZMW",
    payer: { type: "MMO", accountDetails: { phoneNumber: "260763456789", provider: "MTN_MOMO_ZMB" } },
  }));
  const headers = signRequest({
    method: "POST",
    authority: "api.sandbox.pawapay.io",
    path: "/v2/deposits",
    body,
    privateKeyPem: privPem,
    keyId: "DEMO_KEY",
  });
  console.log("--- Signed headers ---");
  for (const [k, v] of Object.entries(headers)) console.log(`${k}: ${v}`);
  console.log("\n--- Public key (PEM) ---");
  console.log(publicKey.export({ format: "pem", type: "spki" }));
}
