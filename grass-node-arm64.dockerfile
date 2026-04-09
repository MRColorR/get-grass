FROM mrcolorrain/vnc-browser:debian

# Install necessary packages then clean up to reduce image size
RUN set -e; \
    apt update && \
    apt upgrade -y && \
    apt install -qqy \
    curl \
    wget \
    git \
    chromium \
    chromium-driver \
    python3 \
    python3-requests \
    python3-selenium \
    coreutils \
    bash && \
    apt autoremove --purge -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Expose VNC and noVNC ports
EXPOSE 5900 6080

# Use the base image's VNC browser environment
# No auto-login: user logs in manually via noVNC on port 6080
ENV CUSTOMIZE=true
ENV AUTO_START_BROWSER=false
ENV AUTO_START_XTERM=false
COPY grass-node-arm64_main.py /app/custom_entrypoints_scripts
