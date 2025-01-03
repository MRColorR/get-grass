FROM debian:stable-slim

# Set environment variables
ENV EXTENSION_ID=ilehaonighjijnmpnagapkhpcdbhclfg
ENV EXTENSION_URL='https://app.getgrass.io/'
ENV GIT_USERNAME=sryze
ENV GIT_REPO=crx-dl

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

# Download crx downloader from git
RUN git clone "https://github.com/${GIT_USERNAME}/${GIT_REPO}.git" && \
    chmod +x ./${GIT_REPO}/crx-dl.py

# Download the extension selected
RUN python3 ./${GIT_REPO}/crx-dl.py $EXTENSION_ID

# Install python requirements
COPY grass_main.py .
# RUN pip install -r requirements.txt
ENTRYPOINT [ "python3", "grass_main.py" ]