# Grass (GetGrass) Docker Container 🚀
🌟 **If you find this project helpful, please consider leaving a star. Your support is appreciated!🙂** 

![Docker Pulls](https://img.shields.io/docker/pulls/mrcolorrain/grass?style=flat-square&link=https://hub.docker.com/r/mrcolorrain/grass)
![Docker Stars](https://img.shields.io/docker/stars/mrcolorrain/grass?style=flat-square&link=https://hub.docker.com/r/mrcolorrain/grass)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/mrcolorr/get-grass/grass_auto_build-push.yml?style=flat&link=https%3A%2F%2Fhub.docker.com%2Fr%2Fmrcolorrain%2Fgrass)

## Introduction 📖
This repository hosts the Dockerfiles and necessary configurations for the unofficial [GetGrass](https://app.getgrass.io/register/?referralCode=qyvJmxgNUhcLo2f) Docker images for grass lite, grass node and grass desktop flavors. It's designed to facilitate the deployment of Grass (GetGrass) in Docker environments, supporting both x86_64 and arm64 architectures.

## Features ✨
- **Debian slim Base Image**: Utilizes the latest version of Debian slim for a small footprint.
- **Multi-Architecture Support**: Supports both x86_64 and arm64 architectures.
- **Minimal Configuration**: Easy to set up with minimal configuration required.
- **Auto-Update**: Always updated to be in line with the latest Grass version.
- **VNC Enabled**: Includes a VNC-based graphical interface to check and optionally interact with Grass.

## Prerequisites 📋
Ensure Docker is installed on your system. For installation instructions, please refer to the [official Docker documentation](https://docs.docker.com/get-docker/).

## Quick Start 🚀
You can run it easily passing the appropriate environment variables.
- ### Docker cli 🐳
  ```bash
  docker run -d --name grass -h my_device -e GRASS_USER=your_email -e GRASS_PASS=your_password mrcolorrain/grass
  ```
- ### Docker compose 🐳
  ```yaml
  version: "3.9"
  services:
    grass:
      container_name: grass
      hostname: my_device
      image: mrcolorrain/grass
      environment:
        - GRASS_USER=your_email
        - GRASS_PASS=your_password
      restart: unless-stopped
  ```
---
## Grass-Node 📦
This section provides instructions on how to use the grass-node extension if you want to use this instead of the standard grass extension available in the other image.
- ### Docker cli 🐳
  ```bash
  docker run -d --name grass-node -h my_device -e USER_EMAIL=your_email -e USER_PASSWORD=your_password -p 5900:5900 -p 6080:6080 mrcolorrain/grass-node
  ```
- ### Docker compose 🐳
  ```yaml
  version: "3.9"
  services:
    grass-node:
      container_name: grass-node
      hostname: my_device
      image: mrcolorrain/grass-node
      environment:
        USER_EMAIL: your_email
        USER_PASSWORD: your_password
      ports:
        - "5900:5900"
        - "6080:6080"
  ```
   _Default vnc password is the default password of [vnc-browser](https://github.com/MRColorR/vnc-browser) image. (Currently it should be: `money4band`)_

---
## Grass-Node ARM64 (Raspberry Pi) 🍓
This is a self-built variant of grass-node designed for ARM64 devices such as the Raspberry Pi. There is no pre-built image on Docker Hub — you must build it locally. This variant does **not** support auto-login; you will log in to your Grass account manually through the noVNC web interface.

- ### Build & Run with Docker CLI 🐳
  ```bash
  docker build -t grass-node-arm64 -f grass-node-arm64.dockerfile .
  docker run -d --name grass --shm-size=256m -p 6080:6080 --restart unless-stopped grass-node-arm64
  ```

- ### Docker compose 🐳
  ```yaml
  services:
    grass-node-arm64:
      build:
        context: .
        dockerfile: grass-node-arm64.dockerfile
      container_name: grass
      shm_size: '256m'
      ports:
        - "6080:6080"
      restart: unless-stopped
  ```
  ```bash
  docker compose -f grass-node-arm64.docker-compose.yaml build && docker compose -f grass-node-arm64.docker-compose.yaml up -d
  ```

### Setting up your account via noVNC
Once the container is running you need to connect to noVNC to log in to your Grass account:
1. Open `http://<your-host-ip>:6080` in a web browser
2. Enter the VNC password when prompted (default: `money4band`)
3. A Chromium browser will appear with the Grass dashboard — log in with your Grass credentials
4. Once logged in, the script automatically detects the connection and begins monitoring it. If the connection drops, the browser will restart and you will need to log in again via noVNC.

  _Default vnc password is the default password of [vnc-browser](https://github.com/MRColorR/vnc-browser) image. (Currently it should be: `money4band`)_

---
## Grass-Desktop 🖥️
we have also a Grass Desktop image available. This section provides instructions on how to use the grass-desktop GUI application fully automated inside a container.  Just in case you want to use this instead of the standard grass-node or grass extension available in the other images. 
_Note: This GUI version is heavier than the other images due to the additional components required to run a full desktop environment._

### Environment Variables
- `USER_EMAIL` or `GRASS_EMAIL` or `GRASS_USER`: Your Grass account email
- `USER_PASSWORD` or `GRASS_PASSWORD` or `GRASS_PASS`: Your Grass account password
- `TRY_AUTOLOGIN`: Set to "true" to enable automatic login. Set to "false" to disable automatic login and require manual interaction.
- `MAX_RETRY_MULTIPLIER`: (Optional) A number to multiply retry timings. Default is 3. Increase this if you experience timing issues with auto-login.

### Docker cli 🐳
  ```bash
  docker run -d --name grass-desktop -h my_device -e USER_EMAIL=your_email -e USER_PASSWORD=your_password -e TRY_AUTOLOGIN=false -p 5900:5900 -p 6080:6080 mrcolorrain/grass-desktop
  ```

### Docker compose 🐳
  ```yaml
  version: "3.9"
  services:
    grass-desktop:
      container_name: grass-desktop
      hostname: my_device
      image: mrcolorrain/grass-desktop
      environment:
        USER_EMAIL: your_email
        USER_PASSWORD: your_password
        TRY_AUTOLOGIN: "false"
      ports:
        - "5900:5900"
        - "6080:6080"
  ```
  _Default vnc password is the default password of [vnc-browser](https://github.com/MRColorR/vnc-browser) image. (Currently it should be: `money4band`)_

  **Note on Auto-Login**: When `TRY_AUTOLOGIN` is enabled, the container will attempt to automatically log in using the provided credentials. If auto-login fails or credentials are missing, it will fall back to manual mode where you can interact with the Grass interface through VNC.


## Contributing 🤲
Your contributions are welcome! If you'd like to improve the project or fix a bug, please fork the repository and submit a pull request. Let's make this project even better, together!

## Disclaimer ⚠️
This is an unofficial build and not affiliated or officially endorsed by Grass (getgrass).
This repository (project) and its assets are provided "as is" without warranty of any kind.
The author makes no warranties, express or implied, that this project and its assets are free of errors, defects, or suitable for any particular purpose.
The author shall not be liable for any damages suffered by any user of this project, whether direct, indirect, incidental, consequential, or special, arising from the use of or inability to use this project, its assets or its documentation, even if the author has been advised of the possibility of such damages.

## License
This program is free software distributed under the terms of the GNU General Public License (GPL-3.0). You can redistribute it and/or modify it under the terms of the license. However, there is no warranty provided, and you use it at your own risk.

## Want more? 💵📈
This image is also part of Money4Band, a free open-source project that runs various passive income apps in a safe, containerized environment. Turn your unused internet bandwidth into earnings! Why let your unused internet bandwidth go to waste? Start earning today! Check out the Money4Band project on [here](https://github.com/MRColorR/money4band) GitHub to get started.
