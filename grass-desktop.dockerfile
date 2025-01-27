# --- Stage 1: Build Stage to Patch Grass Deb ---
    FROM debian:stable-slim AS grass-deb-patcher

    ARG GRASS_VERSION="4.31.2"
    ARG GRASS_ARCH="amd64"
    ARG GRASS_PACKAGE_URL="https://files.getgrass.io/file/grass-extension-upgrades/ubuntu-22.04/Grass_${GRASS_VERSION}_${GRASS_ARCH}.deb"
    
    RUN apt-get update && apt-get install -y --no-install-recommends \
        binutils \
        wget \
        ca-certificates && \
        rm -rf /var/lib/apt/lists/*
    
    RUN mkdir /tmp/grass-fix
    WORKDIR /tmp/grass-fix
    
    # Download and patch Grass package
    RUN wget -q -O /tmp/grass.deb $GRASS_PACKAGE_URL && \
        ar -x /tmp/grass.deb && \
        tar -xzvf control.tar.gz && \
        sed -i 's/Package: grass/Package: getgrass-io/' control && \
        tar -czvf control.tar.gz control md5sums && \
        rm control md5sums && \
        ar r /tmp/grass.deb * && \
        rm -rf /tmp/grass-fix/*
    
    # --- Stage 2: Final Runtime Image ---
    FROM mrcolorrain/vnc-browser:debian

    # Set environment variables
    ENV PYTHONUNBUFFERED=1
    # In case of error multiply all backoff-timings of this value
    ENV MAX_RETRY_MULTIPLIER=3

    # We only install what's needed to run Grass and configure it
    RUN set -e; \
        apt-get update && \
        apt-get install -y --no-install-recommends \
        xdotool \
        ca-certificates \
        dpkg \
        libayatana-appindicator3-1 \
        libwebkit2gtk-4.1-0 \ 
        libgtk-3-0
    
    # Copy patched deb from builder stage
    COPY --from=grass-deb-patcher /tmp/grass.deb /tmp/grass.deb
    
    # Install Grass and fix dependencies
    RUN dpkg -i /tmp/grass.deb || apt-get -y --no-install-recommends --fix-broken install && \
        rm /tmp/grass.deb &&\
        apt autoremove --purge -y && \
        apt clean && \
        rm -rf /var/lib/apt/lists/*
    
    # # Create grass user
    # RUN adduser --disabled-password --gecos "" grass && \
    #     apt autoremove --purge -y && \
    #     apt clean && \
    #     rm -rf /var/lib/apt/lists/*

    # RUN chmod -R 777 /app/
    # USER grass
    # WORKDIR /home/grass
    
    # # Copy the entrypoint wrapper script
    # COPY entrypoint-wrapper.sh /app/entrypoint-wrapper.sh
    # RUN chmod +x /app/entrypoint-wrapper.sh
    
    # Expose VNC and noVNC ports if needed
    EXPOSE 5900 6080
    
    # New base image permits entrypoint customization
    ENV CUSTOMIZE=true
    ENV AUTO_START_BROWSER=false
    ENV AUTO_START_XTERM=false
    COPY grass-desktop_main.py /app/custom_entrypoints_scripts