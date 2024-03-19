FROM debian:stable-slim

# Set environment variables
ENV EXTENSION_ID=ilehaonighjijnmpnagapkhpcdbhclfg
ENV GIT_USERNAME=warren-bank
ENV GIT_REPO=chrome-extension-downloader

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
    python3-selenium && \
    apt autoremove --purge -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Download crx dowloader from git
RUN git clone "https://github.com/${GIT_USERNAME}/${GIT_REPO}.git" && \
    chmod +x ./${GIT_REPO}/bin/*

# Download the extension selected
RUN ./${GIT_REPO}/bin/crxdl $EXTENSION_ID

# Install python requirements
COPY main.py .
# RUN pip install -r requirements.txt
ENTRYPOINT [ "python3", "main.py" ]