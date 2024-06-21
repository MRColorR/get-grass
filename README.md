# Grass (GetGrass) Docker Container 🚀
![Docker Pulls](https://img.shields.io/docker/pulls/mrcolorrain/grass?style=flat-square&link=https://hub.docker.com/r/mrcolorrain/grass)
![Docker Stars](https://img.shields.io/docker/stars/mrcolorrain/grass?style=flat-square&link=https://hub.docker.com/r/mrcolorrain/grass)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/mrcolorr/get-grass/grass_docker-publish.yml?style=flat&link=https%3A%2F%2Fhub.docker.com%2Fr%2Fmrcolorrain%2Fgrass)

🌟 **If you find this project helpful, please consider leaving a star. Your support is appreciated!🙂** 

## Introduction 📖
This repository hosts the Dockerfile and necessary configurations for the unofficial [GetGrass](https://app.getgrass.io/register/?referralCode=qyvJmxgNUhcLo2f) Docker image. It's designed to facilitate the deployment of Grass (GetGrass) in Docker environments, supporting both x86_64 and arm64 architectures.

## Features ✨
- **Debian slim Base Image**: Utilizes the latest version of Debian slim for a small footprint.
- **Multi-Architecture Support**: Supports both x86_64 and arm64 architectures.
- **Minimal Configuration**: Easy to set up with minimal configuration required.
- **Auto-Update**: Always updated to be in line with the latest Grass version.

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
  docker run -d --name grass-node -h my_device -e USER_EMAIL=your_email -e USER_PASSWORD=your_password -p 8080:8080 mrcolorrain/grass-node
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
        - "8080:8080"
      tty: true
  ```


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
