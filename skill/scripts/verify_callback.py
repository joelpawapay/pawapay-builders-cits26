"""
scripts/verify_callback.py — Verify an inbound RFC 9421 signed callback from pawaPay.

Use this in your callback handler to confirm the request actually came from pawaPay
and the body wasn't tampered with.

Dependencies:
    pip install cryptography

Usage in a Flask handler:

    from sign_request import verify_callback  # this file
    from flask import request

    @app.post("/pawapay/callback")
    def callback():
        raw = request.get_data()  # raw bytes; do NOT re-serialise
        try:
            verify_callback(
                method=request.method,
                authority=request.host,
                path=request.path,
                headers=request.headers,
                body=raw,
                public_key_resolver=get_pawapay_public_key,
            )
        except VerificationError as e:
            return ("invalid signature: " + str(e), 401)
        ...

`public_key_resolver(keyid: str) -> bytes` returns the public-key PEM for the given
keyid. Typically fetches & caches `GET /v2/public-key/http` and matches on the `id`.
"""

from __future__ import annotations

import base64
import hashlib
import re
import time
from typing import Callable, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature


class VerificationError(Exception):
    pass


PublicKeyResolver = Callable[[str], bytes]


def verify_callback(
    *,
    method: str,
    authority: str,
    path: str,
    headers: Mapping[str, str],
    body: bytes,
    public_key_resolver: PublicKeyResolver,
    max_age_seconds: int = 600,  # reject signatures older than this
) -> None:
    """Raise VerificationError if the signature does not verify."""
    # Header lookups are case-insensitive.
    h = _CaseInsensitive(headers)

    signature_input = h.get("Signature-Input")
    signature_header = h.get("Signature")
    content_digest = h.get("Content-Digest")
    signature_date = h.get("Signature-Date")
    content_type = h.get("Content-Type")

    if not signature_input or not signature_header:
        raise VerificationError("missing Signature or Signature-Input header")
    if not content_digest:
        raise VerificationError("missing Content-Digest header")

    # 1. Verify Content-Digest matches the body.
    _verify_content_digest(content_digest, body)

    # 2. Parse Signature-Input.
    label, covered, params = _parse_signature_input(signature_input)
    alg = params.get("alg")
    keyid = params.get("keyid")
    created = int(params.get("created", "0") or "0")
    expires = int(params.get("expires", "0") or "0")

    if not alg or not keyid:
        raise VerificationError("Signature-Input missing alg or keyid")

    # 3. Freshness check.
    now = int(time.time())
    if created and now - created > max_age_seconds:
        raise VerificationError(f"signature is stale (created={created}, now={now})")
    if expires and now > expires:
        raise VerificationError(f"signature expired (expires={expires}, now={now})")

    # 4. Resolve the public key.
    pub_pem = public_key_resolver(keyid)
    if not pub_pem:
        raise VerificationError(f"unknown keyid: {keyid}")

    # 5. Reconstruct the signature base.
    component_values: list[str] = []
    for component in covered:
        if component == "@method":
            component_values.append(f'"@method": {method.upper()}')
        elif component == "@authority":
            component_values.append(f'"@authority": {authority}')
        elif component == "@path":
            component_values.append(f'"@path": {path}')
        elif component == "content-digest":
            component_values.append(f'"content-digest": {content_digest}')
        elif component == "signature-date":
            if not signature_date:
                raise VerificationError("signature-date header missing but covered")
            component_values.append(f'"signature-date": {signature_date}')
        elif component == "content-type":
            if not content_type:
                raise VerificationError("content-type header missing but covered")
            component_values.append(f'"content-type": {content_type}')
        else:
            # Generic header lookup
            val = h.get(component)
            if val is None:
                raise VerificationError(f"covered header '{component}' missing")
            component_values.append(f'"{component}": {val}')

    sig_params_str = signature_input.split("=", 1)[1]  # everything after the label=
    signature_base = "\n".join(component_values + [f'"@signature-params": {sig_params_str}'])

    # 6. Decode the signature from the Signature header.
    raw_sig = _extract_signature_bytes(signature_header, label)

    # 7. Verify with the appropriate algorithm.
    pub = serialization.load_pem_public_key(pub_pem)
    try:
        _verify(pub, signature_base.encode("utf-8"), raw_sig, alg)
    except InvalidSignature as e:
        raise VerificationError("signature did not verify") from e


# ----- helpers -----


class _CaseInsensitive:
    def __init__(self, source: Mapping[str, str]):
        self._lower = {k.lower(): v for k, v in source.items()}

    def get(self, key: str) -> str | None:
        return self._lower.get(key.lower())


def _verify_content_digest(content_digest: str, body: bytes) -> None:
    # Format: "sha-512=:base64:"  (or sha-256)
    m = re.match(r"^(sha-256|sha-512)=:([A-Za-z0-9+/=]+):$", content_digest.strip())
    if not m:
        raise VerificationError(f"malformed Content-Digest: {content_digest!r}")
    alg, b64 = m.group(1), m.group(2)
    expected = hashlib.sha256(body).digest() if alg == "sha-256" else hashlib.sha512(body).digest()
    actual = base64.b64decode(b64)
    if expected != actual:
        raise VerificationError("Content-Digest does not match body")


def _parse_signature_input(value: str) -> tuple[str, list[str], dict[str, str]]:
    # Example: sig-pp=("@method" "@authority" "@path" "signature-date" "content-digest" "content-type");alg="ecdsa-p256-sha256";keyid="CUSTOMER_TEST_KEY";created=1714657551;expires=1714657611
    m = re.match(r'^([A-Za-z0-9_-]+)=\((.*?)\)(.*)$', value)
    if not m:
        raise VerificationError(f"malformed Signature-Input: {value!r}")
    label = m.group(1)
    covered_str = m.group(2)
    params_str = m.group(3)
    covered = [c.strip().strip('"') for c in covered_str.split(" ") if c.strip()]
    params: dict[str, str] = {}
    for part in params_str.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        params[k.strip()] = v.strip().strip('"')
    return label, covered, params


def _extract_signature_bytes(signature_header: str, expected_label: str) -> bytes:
    # Example: sig-pp=:base64:
    m = re.match(rf"^{re.escape(expected_label)}=:([A-Za-z0-9+/=]+):$", signature_header.strip())
    if not m:
        # Fallback: accept any label, in case pawaPay uses a different one.
        m = re.match(r"^[A-Za-z0-9_-]+=:([A-Za-z0-9+/=]+):$", signature_header.strip())
        if not m:
            raise VerificationError(f"malformed Signature: {signature_header!r}")
    return base64.b64decode(m.group(1))


def _verify(public_key, base: bytes, raw_signature: bytes, algorithm: str) -> None:
    if algorithm == "ecdsa-p256-sha256":
        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            raise VerificationError("public key is not ECDSA")
        r, s = _ecdsa_raw_to_rs(raw_signature, byte_length=32)
        der = encode_dss_signature(r, s)
        public_key.verify(der, base, ec.ECDSA(hashes.SHA256()))
        return
    if algorithm == "ecdsa-p384-sha384":
        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            raise VerificationError("public key is not ECDSA")
        r, s = _ecdsa_raw_to_rs(raw_signature, byte_length=48)
        der = encode_dss_signature(r, s)
        public_key.verify(der, base, ec.ECDSA(hashes.SHA384()))
        return
    if algorithm == "rsa-pss-sha512":
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise VerificationError("public key is not RSA")
        public_key.verify(
            raw_signature,
            base,
            padding.PSS(mgf=padding.MGF1(hashes.SHA512()), salt_length=64),
            hashes.SHA512(),
        )
        return
    if algorithm == "rsa-v1_5-sha256":
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise VerificationError("public key is not RSA")
        public_key.verify(raw_signature, base, padding.PKCS1v15(), hashes.SHA256())
        return
    raise VerificationError(f"unsupported alg: {algorithm}")


def _ecdsa_raw_to_rs(raw: bytes, *, byte_length: int) -> tuple[int, int]:
    if len(raw) != 2 * byte_length:
        raise VerificationError(f"ECDSA raw signature wrong length: {len(raw)}")
    r = int.from_bytes(raw[:byte_length], "big")
    s = int.from_bytes(raw[byte_length:], "big")
    return r, s


# Smoke-test: run after sign_request.py to verify a self-signed callback works.
if __name__ == "__main__":
    import sys

    print("verify_callback.py — import and use verify_callback() in your handler.")
    print("Run `python sign_request.py` to see an example signed request.")
    sys.exit(0)
