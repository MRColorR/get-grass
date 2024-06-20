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
    python3-selenium \
    coreutils \
    bash && \
    apt autoremove --purge -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY grass-node_requirements.txt /app/grass-node_requirements.txt
RUN pip3 install -r /app/grass-node_requirements.txt

# Copy only the main Python script
COPY grass-node_main.py /app/grass-node_main.py
WORKDIR /app
ENTRYPOINT [ "python3", "grass-node_main.py" ]
