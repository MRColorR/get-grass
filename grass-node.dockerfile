FROM theasp/novnc:latest

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
    python3-requests \
    python3-selenium \
    coreutils \
    bash && \
    apt autoremove --purge -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only the main Python script
COPY grass-node_main.py /app/grass-node_main.py
WORKDIR /app

#Expose noVNC port
EXPOSE  8080

# Start app
ENTRYPOINT [ "python3", "grass-node_main.py" ]