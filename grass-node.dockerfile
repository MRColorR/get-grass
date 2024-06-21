FROM theasp/novnc:latest

# Set environment variables
ENV EXTENSION_ID=grass
ENV EXTENSION_URL='https://app.getgrass.io/'

# Install necessary packages then clean up to reduce image size
RUN set -ex; \
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
COPY grass-node_main.py /app/grass-node_main.py
#COPY conf.d/grass-node.conf /app/conf.d/grass-node.conf

# Copy the entrypoint wrapper script
COPY entrypoint-wrapper.sh /app/entrypoint-wrapper.sh
RUN chmod +x /app/entrypoint-wrapper.sh

WORKDIR /app

# Expose noVNC port
EXPOSE 8080

# Use the base image's entrypoint
ENTRYPOINT ["/app/entrypoint-wrapper.sh"]
