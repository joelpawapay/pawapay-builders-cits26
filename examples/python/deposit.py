"""Collect a mobile money payment (a deposit) on the pawaPay sandbox.

Python 3.8+, standard library only. No pip install needed.

Run from the examples/ folder:
    python3 python/deposit.py [phoneNumber] [amount]
    python3 python/deposit.py 237653456789 1000
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

# Load .env from the current folder into os.environ.
if os.path.exists(".env"):
    with open(".env") as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

TOKEN = os.environ.get("PAWAPAY_API_TOKEN", "")
BASE_URL = os.environ.get("PAWAPAY_BASE_URL", "https://api.sandbox.pawapay.io")
TEAM = os.environ.get("PAWAPAY_TEAM", "team-unknown")

if not TOKEN or TOKEN.startswith("paste-"):
    sys.exit("Set PAWAPAY_API_TOKEN in examples/.env first. See getting-started.md.")


def stop(message):
    print(f"pawaPay said: {message}", file=sys.stderr)
    if "AUTHENTICATION" in message or "AUTHORISATION" in message:
        print("Check PAWAPAY_API_TOKEN in examples/.env. It must be a sandbox token.", file=sys.stderr)
    sys.exit(1)


def pawapay(method, path, body=None):
    request = urllib.request.Request(
        BASE_URL + path,
        method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.load(response)
    except urllib.error.URLError as error:
        if not isinstance(error, urllib.error.HTTPError):
            stop(f"network error: {error.reason}")
        data = json.loads(error.read() or b"{}")
        if "failureReason" not in data:
            stop(f"HTTP {error.code}: {data}")
    if data.get("failureReason"):
        reason = data["failureReason"]
        stop(f"{reason['failureCode']}: {reason['failureMessage']}")
    return data


phone_input = sys.argv[1] if len(sys.argv) > 1 else "237653456789"
amount = sys.argv[2] if len(sys.argv) > 2 else "1000"

# 1. Clean up the phone number and find out which operator it belongs to.
predicted = pawapay("POST", "/v2/predict-provider", {"phoneNumber": phone_input})
print(f"Phone {predicted['phoneNumber']} is on {predicted['provider']}")

# 2. Create the deposit ID yourself. In a real app, save it to your database now.
deposit_id = str(uuid.uuid4())

# 3. Ask pawaPay to collect the money.
initiated = pawapay("POST", "/v2/deposits", {
    "depositId": deposit_id,
    "amount": amount,  # a string, never a number. XAF has no decimals.
    "currency": "XAF",
    "payer": {
        "type": "MMO",
        "accountDetails": {
            "phoneNumber": predicted["phoneNumber"],
            "provider": predicted["provider"],
        },
    },
    "customerMessage": "CITS26 test",
    "metadata": [{"team": TEAM}],
})
print(f"Deposit {deposit_id}: {initiated['status']}")
if initiated["status"] != "ACCEPTED":
    sys.exit(1)

# 4. ACCEPTED is not paid. Poll until the deposit reaches COMPLETED or FAILED.
for attempt in range(1, 21):
    time.sleep(3)
    check = pawapay("GET", f"/v2/deposits/{deposit_id}")
    status = check["data"]["status"] if check["status"] == "FOUND" else check["status"]
    print(f"  check {attempt}: {status}")

    if status == "COMPLETED":
        print("Payment received. Deliver the goods.")
        sys.exit(0)
    if status == "FAILED":
        reason = check["data"].get("failureReason") or {}
        print(f"Payment failed: {reason.get('failureCode')} ({reason.get('failureMessage')})")
        sys.exit(1)

print("Still pending after 60 seconds. Check again later with the deposit ID above.")
