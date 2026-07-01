# OpenVSP headless API — built for Railway (Ubuntu 24.04 base)
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

ARG OPENVSP_VERSION=3.51.0
ARG OPENVSP_DEB_URL=https://openvsp.org/zips/current/linux/OpenVSP-${OPENVSP_VERSION}-Ubuntu-24.04_amd64.deb

# System deps: Python venv for openvsp-mcp (avoids apt pip upgrade conflicts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    python3 \
    python3-dev \
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

# Confirm OpenVSP binaries exist (vsp --version is not a valid CLI flag)
RUN test -x /usr/local/bin/vsp \
    && test -x /usr/local/bin/vspaero \
    && echo "OpenVSP binaries: /usr/local/bin/vsp, /usr/local/bin/vspaero"

# REST wrapper around OpenVSP (FastAPI).
# Use a venv — Ubuntu's apt-installed pip cannot be upgraded in-place.
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install --no-cache-dir \
    "git+https://github.com/Three-Little-Birds/openvsp-mcp.git" \
    "uvicorn[standard]>=0.30"

ENV PATH="/opt/venv/bin:$PATH"

ENV OPENVSP_BIN=/usr/local/bin/vsp
ENV VSPAERO_BIN=/usr/local/bin/vspaero
ENV GEOMETRY_DIR=/data/geometry
ENV RESULTS_DIR=/data/results

WORKDIR /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f "http://127.0.0.1:${PORT:-8000}/health" || exit 1

COPY entrypoint.sh /usr/local/bin/docker-entrypoint.sh
# Strip Windows CRLF if present — otherwise Linux sees shebang as /bin/sh\r
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh \
    && chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/bin/sh", "/usr/local/bin/docker-entrypoint.sh"]
