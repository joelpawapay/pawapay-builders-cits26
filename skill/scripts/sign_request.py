"""
scripts/sign_request.py — RFC 9421 message signature for pawaPay Merchant API v2.

Default: ECDSA P-256 with SHA-256 over signature base, SHA-512 for the Content-Digest.

Dependencies:
    pip install cryptography

Usage:
    from sign_request import sign_request
    headers = sign_request(
        method="POST",
        authority="api.sandbox.pawapay.io",
        path="/v2/deposits",
        body=body_bytes,                # bytes — the exact body you will send
        private_key_pem=open("private.pem", "rb").read(),
        key_id="CUSTOMER_TEST_KEY",
    )
    # → dict of {Content-Digest, Signature-Date, Signature, Signature-Input,
    #             Accept-Signature, Accept-Digest}.
    # Send headers along with Authorization + Content-Type with the same body bytes.

IMPORTANT: pawaPay signs the EXACT bytes you submit. Don't re-serialise the JSON
between signing and sending — keep one immutable bytes object and pass it to both.
"""

from __future__ import annotations

import base64
import hashlib
import time
from datetime import datetime, timezone
from typing import Literal, Mapping

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)


ACCEPT_SIGNATURE = "rsa-pss-sha512,ecdsa-p256-sha256,rsa-v1_5-sha256,ecdsa-p384-sha384"
ACCEPT_DIGEST = "sha-256,sha-512"

Algorithm = Literal[
    "ecdsa-p256-sha256",
    "ecdsa-p384-sha384",
    "rsa-pss-sha512",
    "rsa-v1_5-sha256",
]


def sign_request(
    *,
    method: str,
    authority: str,
    path: str,
    body: bytes,
    private_key_pem: bytes,
    key_id: str,
    algorithm: Algorithm = "ecdsa-p256-sha256",
    digest_algorithm: Literal["sha-256", "sha-512"] = "sha-512",
    lifetime_seconds: int = 60,
    content_type: str = "application/json; charset=UTF-8",
) -> Mapping[str, str]:
    if not isinstance(body, (bytes, bytearray)):
        raise TypeError("body must be bytes")

    # 1. Content-Digest
    digest = hashlib.sha256(body).digest() if digest_algorithm == "sha-256" else hashlib.sha512(body).digest()
    digest_b64 = base64.b64encode(digest).decode("ascii")
    content_digest = f"{digest_algorithm}=:{digest_b64}:"

    # 2. Timestamps
    created = int(time.time())
    expires = created + lifetime_seconds
    signature_date = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")

    # 3. Build covered components and signature-input parameter string
    components = [
        f'"@method": {method.upper()}',
        f'"@authority": {authority}',
        f'"@path": {path}',
        f'"signature-date": {signature_date}',
        f'"content-digest": {content_digest}',
        f'"content-type": {content_type}',
    ]
    covered_list = '("@method" "@authority" "@path" "signature-date" "content-digest" "content-type")'
    sig_params = (
        f'{covered_list};alg="{algorithm}";keyid="{key_id}";'
        f"created={created};expires={expires}"
    )

    # 4. Signature base — components joined by newline, with @signature-params last.
    signature_base = "\n".join(components + [f'"@signature-params": {sig_params}'])

    # 5. Sign
    signature_b64 = _sign(signature_base.encode("utf-8"), private_key_pem, algorithm)

    # 6. Return headers
    return {
        "Content-Digest": content_digest,
        "Signature-Date": signature_date,
        "Signature": f"sig-pp=:{signature_b64}:",
        "Signature-Input": f"sig-pp={sig_params}",
        "Accept-Signature": ACCEPT_SIGNATURE,
        "Accept-Digest": ACCEPT_DIGEST,
    }


def _sign(signature_base: bytes, private_key_pem: bytes, algorithm: Algorithm) -> str:
    key = serialization.load_pem_private_key(private_key_pem, password=None)

    if algorithm == "ecdsa-p256-sha256":
        if not isinstance(key, ec.EllipticCurvePrivateKey):
            raise TypeError("ecdsa-p256-sha256 requires an ECDSA P-256 private key")
        der_sig = key.sign(signature_base, ec.ECDSA(hashes.SHA256()))
        raw = _ecdsa_der_to_raw(der_sig, byte_length=32)
        return base64.b64encode(raw).decode("ascii")

    if algorithm == "ecdsa-p384-sha384":
        if not isinstance(key, ec.EllipticCurvePrivateKey):
            raise TypeError("ecdsa-p384-sha384 requires an ECDSA P-384 private key")
        der_sig = key.sign(signature_base, ec.ECDSA(hashes.SHA384()))
        raw = _ecdsa_der_to_raw(der_sig, byte_length=48)
        return base64.b64encode(raw).decode("ascii")

    if algorithm == "rsa-pss-sha512":
        if not isinstance(key, rsa.RSAPrivateKey):
            raise TypeError("rsa-pss-sha512 requires an RSA private key")
        sig = key.sign(
            signature_base,
            padding.PSS(mgf=padding.MGF1(hashes.SHA512()), salt_length=64),
            hashes.SHA512(),
        )
        return base64.b64encode(sig).decode("ascii")

    if algorithm == "rsa-v1_5-sha256":
        if not isinstance(key, rsa.RSAPrivateKey):
            raise TypeError("rsa-v1_5-sha256 requires an RSA private key")
        sig = key.sign(signature_base, padding.PKCS1v15(), hashes.SHA256())
        return base64.b64encode(sig).decode("ascii")

    raise ValueError(f"Unsupported algorithm: {algorithm}")


def _ecdsa_der_to_raw(der_signature: bytes, *, byte_length: int) -> bytes:
    """Convert a DER-encoded ECDSA signature to the raw r||s form RFC 9421 requires."""
    r, s = decode_dss_signature(der_signature)
    return r.to_bytes(byte_length, "big") + s.to_bytes(byte_length, "big")


# CLI smoke-test:  python sign_request.py
if __name__ == "__main__":
    from cryptography.hazmat.primitives.asymmetric import ec

    # Generate a throwaway key.
    priv = ec.generate_private_key(ec.SECP256R1())
    priv_pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    body = (
        b'{"depositId":"f4401bd2-1568-4140-bf2d-eb77d2b2b639","amount":"15",'
        b'"currency":"ZMW","payer":{"type":"MMO","accountDetails":'
        b'{"phoneNumber":"260763456789","provider":"MTN_MOMO_ZMB"}}}'
    )

    headers = sign_request(
        method="POST",
        authority="api.sandbox.pawapay.io",
        path="/v2/deposits",
        body=body,
        private_key_pem=priv_pem,
        key_id="DEMO_KEY",
    )
    print("--- Signed headers ---")
    for k, v in headers.items():
        print(f"{k}: {v}")
    print("\n--- Public key (PEM) ---")
    print(pub_pem.decode())
