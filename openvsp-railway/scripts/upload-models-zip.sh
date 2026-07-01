#!/bin/sh
# Upload uav-models.zip to Railway via HTTP (one request, ~1 second).
set -e

API_URL="${OPENVSP_API_URL:-https://openvsp-api-production.up.railway.app}"
ZIP="$(cd "$(dirname "$0")/.." && pwd)/models/uav-models.zip"
TOKEN="${UPLOAD_TOKEN:-}"

if [ ! -f "$ZIP" ]; then
  echo "Missing $ZIP — run: cd openvsp-railway/models/staging && zip first"
  exit 1
fi

echo "Uploading $(du -h "$ZIP" | cut -f1) to $API_URL/api/upload-zip"

if [ -n "$TOKEN" ]; then
  curl -sf -X POST "$API_URL/api/upload-zip?token=$TOKEN" \
    -F "file=@$ZIP;filename=uav-models.zip"
else
  curl -sf -X POST "$API_URL/api/upload-zip" \
    -F "file=@$ZIP;filename=uav-models.zip"
fi

echo ""
echo "Done."
