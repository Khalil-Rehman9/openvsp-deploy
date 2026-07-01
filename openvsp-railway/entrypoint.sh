#!/bin/sh
set -e

# Railway injects PORT; default to 8000 for local runs
PORT="${PORT:-8000}"

# Fall back if .deb installed binaries elsewhere
if [ ! -x "$OPENVSP_BIN" ]; then
  OPENVSP_BIN="$(command -v vsp || command -v vspscript || true)"
  export OPENVSP_BIN
fi

if [ ! -x "$VSPAERO_BIN" ]; then
  VSPAERO_BIN="$(command -v vspaero || true)"
  export VSPAERO_BIN
fi

echo "Starting OpenVSP API on port ${PORT}"
echo "  OPENVSP_BIN=${OPENVSP_BIN}"
echo "  VSPAERO_BIN=${VSPAERO_BIN}"

exec uvicorn openvsp_mcp.fastapi_app:create_app \
  --factory \
  --host 0.0.0.0 \
  --port "${PORT}"
