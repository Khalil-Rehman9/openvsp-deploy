# OpenVSP headless API — built for Railway (Ubuntu 24.04 base)
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

ARG OPENVSP_VERSION=3.51.0
ARG OPENVSP_DEB_URL=https://openvsp.org/zips/current/linux/OpenVSP-${OPENVSP_VERSION}-Ubuntu-24.04_amd64.deb

# System deps: Python for openvsp-mcp REST API
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install official OpenVSP .deb (includes vsp, vspscript, vspaero).
# The .deb postinst calls desktop-file-install for a .desktop menu entry;
# desktop-file-utils must be present or dpkg configure fails in Docker.
RUN wget -q -O /tmp/openvsp.deb "${OPENVSP_DEB_URL}" \
    && apt-get update \
    && apt-get install -y --no-install-recommends desktop-file-utils \
    && apt-get install -y /tmp/openvsp.deb \
    && rm /tmp/openvsp.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Resolve binary paths (deb may install to /usr/bin or /usr/local/bin)
RUN VSP_PATH="$(command -v vsp || command -v vspscript || true)" \
    && test -n "$VSP_PATH" \
    && echo "OpenVSP binary: $VSP_PATH" \
    && "$VSP_PATH" --version || true

# REST wrapper around OpenVSP (FastAPI)
RUN pip3 install --no-cache-dir --break-system-packages \
    "git+https://github.com/Three-Little-Birds/openvsp-mcp.git" \
    "uvicorn[standard]>=0.30"

ENV OPENVSP_BIN=/usr/local/bin/vsp
ENV VSPAERO_BIN=/usr/local/bin/vspaero
ENV GEOMETRY_DIR=/data/geometry
ENV RESULTS_DIR=/data/results

RUN mkdir -p /data/geometry /data/results

WORKDIR /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f "http://127.0.0.1:${PORT:-8000}/health" || exit 1

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
