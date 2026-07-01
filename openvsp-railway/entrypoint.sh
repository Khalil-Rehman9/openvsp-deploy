#!/bin/sh
set -e

# Volume mount at /data replaces image dirs — recreate at runtime
mkdir -p /data/geometry /data/results

# Bootstrap .vsp3 models from zip baked into image (fast — no SSH upload needed)
if [ -f /opt/bootstrap/uav-models.zip ]; then
  if [ ! -s /data/geometry/hero-400ec.vsp3 ]; then
    echo "Extracting UAV models from uav-models.zip ..."
    unzip -o -q /opt/bootstrap/uav-models.zip -d /data/geometry
    ls -lh /data/geometry/*.vsp3 2>/dev/null || true
  fi
fi

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

exec uvicorn api.main:create_app \
  --factory \
  --host 0.0.0.0 \
  --port "${PORT}"
