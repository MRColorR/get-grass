FROM debian:stable-slim

# Set environment variables
ENV EXTENSION_ID=grass
ENV EXTENSION_URL='https://app.getgrass.io/'

# Install necessary packages then clean up to reduce image size
RUN apt update && \
    apt upgrade -y && \
    apt install -qqy \
    curl \
    wget \
    git \
    chromium \
    chromium-driver \
    python3 \
    python3-pip \
    python3-selenium && \
    apt autoremove --purge -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the main Python script
COPY grass-node_main.py .
ENTRYPOINT [ "python3", "grass-node_main.py" ]
