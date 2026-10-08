#!/usr/bin/env bash
# Collect a mobile money payment (a deposit) on the pawaPay sandbox with curl.
# Needs bash, curl, and uuidgen (or python3).
#
# Run from the examples/ folder:
#   bash curl/deposit.sh [phoneNumber] [amount]

set -euo pipefail

if [ -f .env ]; then set -a; . ./.env; set +a; fi

: "${PAWAPAY_API_TOKEN:?Set PAWAPAY_API_TOKEN in examples/.env first. See getting-started.md.}"
BASE_URL="${PAWAPAY_BASE_URL:-https://api.sandbox.pawapay.io}"
TEAM="${PAWAPAY_TEAM:-team-unknown}"
PHONE="${1:-237653456789}"
AMOUNT="${2:-1000}"

DEPOSIT_ID="$(uuidgen 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())')"
DEPOSIT_ID="$(echo "$DEPOSIT_ID" | tr 'A-Z' 'a-z')"

echo "1. Predict the operator for $PHONE"
curl -s -X POST "$BASE_URL/v2/predict-provider" \
  -H "Authorization: Bearer $PAWAPAY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"phoneNumber\": \"$PHONE\"}"
echo

echo "2. Start deposit $DEPOSIT_ID (assumes MTN_MOMO_CMR; use the provider from step 1)"
curl -s -X POST "$BASE_URL/v2/deposits" \
  -H "Authorization: Bearer $PAWAPAY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"depositId\": \"$DEPOSIT_ID\",
    \"amount\": \"$AMOUNT\",
    \"currency\": \"XAF\",
    \"payer\": {
      \"type\": \"MMO\",
      \"accountDetails\": { \"phoneNumber\": \"$PHONE\", \"provider\": \"MTN_MOMO_CMR\" }
    },
    \"customerMessage\": \"CITS26 test\",
    \"metadata\": [ { \"team\": \"$TEAM\" } ]
  }"
echo

echo "3. Wait 5 seconds, then check the status"
sleep 5
curl -s "$BASE_URL/v2/deposits/$DEPOSIT_ID" \
  -H "Authorization: Bearer $PAWAPAY_API_TOKEN"
echo
