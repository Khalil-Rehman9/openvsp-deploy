#!/bin/sh
# Fast upload of UAV .vsp3 models to Railway via HTTP multipart (seconds, not minutes).
set -e

API_URL="${OPENVSP_API_URL:-https://openvsp-api-production.up.railway.app}"
TOKEN="${UPLOAD_TOKEN:-}"
BASE="$(cd "$(dirname "$0")/../Newfolder" && pwd)"

upload() {
  src="$1"
  name="$2"
  echo "→ $name ($(du -h "$src" | cut -f1))"
  if [ -n "$TOKEN" ]; then
    curl -sf -X POST "$API_URL/api/upload?token=$TOKEN" \
      -F "file=@$src;filename=$name"
  else
    curl -sf -X POST "$API_URL/api/upload" \
      -F "file=@$src;filename=$name"
  fi
  echo ""
}

echo "Uploading to $API_URL/api/upload"
echo ""

upload "$BASE/fyp/uavanalysis/Hero400EC_updated.vsp3" "hero-400ec.vsp3"
upload "$BASE/fyp/uavanalysis/Shahed136_updated.vsp3" "shahed-136.vsp3"
upload "$BASE/shadow_heron/testing2/AAI_Shadow_200_updated.vsp3" "aai-shadow.vsp3"
upload "$BASE/shadow_heron/testing2/IAI_Heron_updated.vsp3" "iai-heron.vsp3"

echo "Done. Verify:"
echo "  curl $API_URL/health"
