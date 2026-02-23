#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <w1|w2|w3|w4> <webinar_url>"
  exit 1
fi

TARGET_ID="$1"
WEBINAR_URL="$2"

case "$TARGET_ID" in
  w1|w2|w3|w4) ;;
  *)
    echo "Invalid target. Use one of: w1 w2 w3 w4"
    exit 1
    ;;
esac

/usr/bin/python3 /srv/Eseminar/sync_webinar_target.py \
  --url "$WEBINAR_URL" \
  --out "/srv/Eseminar/targets/${TARGET_ID}.json"

echo "Updated ${TARGET_ID} from ${WEBINAR_URL}"
