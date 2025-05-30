FROM mrcolorrain/vnc-browser:debian

# Set environment variables for extension
ENV EXTENSION_ID=ilehaonighjijnmpnagapkhpcdbhclfg
ENV EXTENSION_URL='https://app.getgrass.io/'
ENV CRX_DOWNLOAD_URL='https://chromewebstore.google.com/detail/grass-lite-node/ilehaonighjijnmpnagapkhpcdbhclfg'

# Extension configuration
# Comma-separated list of extension IDs (extension chrome webstore id)
ENV EXTENSION_IDS=${EXTENSION_ID}
# Comma-separated list of extension URLs (app dashboard website url)
ENV EXTENSION_URLS=${EXTENSION_URL}
# Comma-separated list of CRX download URLs (either direct URLs or Chrome Web Store URLs)
ENV CRX_DOWNLOAD_URLS=${CRX_DOWNLOAD_URL}

# Default configuration
# In case of error multiply all backoff-timings of this value
ENV MAX_RETRY_MULTIPLIER=3
# Define whether to try autologin (true) or go directly to manual mode (false)
ENV TRY_AUTOLOGIN=true
ENV HEADLESS=false
ENV REQUIRE_AUTH_FOR_DOWNLOADS=false

# Git configuration for extension download
ENV GIT_USERNAME=sryze
ENV GIT_REPO=crx-dl


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

# # Download crx downloader from git
# RUN git clone "https://github.com/${GIT_USERNAME}/${GIT_REPO}.git" && \
#     chmod +x ./${GIT_REPO}/crx-dl.py

# # Download the extension selected
# RUN python3 ./${GIT_REPO}/crx-dl.py $EXTENSION_ID

# Set up working directory
WORKDIR /app

# Copy the script to custom entrypoints directory (used by base image)
COPY grass_main.py /app/custom_entrypoints_scripts/grass_main.py

# New base image permits entrypoint customization
ENV CUSTOMIZE=true
ENV AUTO_START_BROWSER=false
ENV AUTO_START_XTERM=false

# Expose VNC and noVNC ports
EXPOSE 5900 6080