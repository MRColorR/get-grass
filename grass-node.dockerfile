FROM mrcolorrain/vnc-browser:debian

# Set build arguments for extensions
ARG EXTENSION_IDS
ARG EXTENSION_URLS
ARG CRX_DOWNLOAD_URLS

# Extension configuration

# Comma-separated list of extension IDs (extension chrome webstore id)
ENV EXTENSION_IDS=${EXTENSION_IDS}
# Comma-separated list of extension URLs (app dashboard website url)
ENV EXTENSION_URLS=${EXTENSION_URLS}
# Comma-separated list of CRX download URLs (either direct URLs or Chrome Web Store URLs)
ENV CRX_DOWNLOAD_URLS=${CRX_DOWNLOAD_URLS}

# Default configuration
# In case of error multiply all backoff-timings of this value
ENV MAX_RETRY_MULTIPLIER=3
# Define whether to try autologin (true) or go directly to manual mode (false)
ENV TRY_AUTOLOGIN=true
ENV HEADLESS=false
ENV REQUIRE_AUTH_FOR_DOWNLOADS=false


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

# Copy the Supervisor configuration and Python script
COPY grass_main.py /app/grass_main.py

WORKDIR /app

# Expose VNC and noVNC ports
EXPOSE 5900 6080 

# New base image permits entrypoint customization
ENV CUSTOMIZE=true
ENV AUTO_START_BROWSER=false
ENV AUTO_START_XTERM=false
COPY grass_main.py /app/custom_entrypoints_scripts/grass_main.py