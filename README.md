# GetGrass Docker Image

An unofficial Docker Image for [grass](https://app.getgrass.io/register/?referralCode=LxGryHB0y3gmNml). 


## Getting Started

1. **Clone the Repository**:
   - First, clone the files from this repository to your local device:

     ```bash
     git clone https://github.com/Carbon2029/get-grass-docker-unofficial.git
     ```

2. **Build the Docker Image**:
   - Navigate to the folder where the cloned files are located.
   - Build the Docker image using the following command:

     ```docker build -t grass .```

3. **Run the Docker Container**:
   - Now you can run the Docker container with the appropriate environment variables.
   - Replace `<your_email>` and `<your_password>` with your actual Grass account credentials:

     ```bash
      docker run -d -e USER=<your_email> -e PASS=<your_password> grass
      ```


## Some random questions 

Is it lightweight?
- As of now no,cpu usage is around 0.01 - 1% and ram usage is around 275 mb will improve it eventually(if I get time or if I get paid ;) )


## License

This program is free software distributed under the terms of the GNU General Public License (GPL-3.0). You can redistribute it and/or modify it under the terms of the license. However, there is no warranty provided, and you use it at your own risk.

## Disclaimer
This script is provided "as is" and without warranty of any kind.
The author makes no warranties, express or implied, that this script is free of errors, defects, or suitable for any particular purpose.
The author shall not be liable for any damages suffered by any user of this script, whether direct, indirect, incidental, consequential, or special, arising from the use of or inability to use this script or its documentation, even if the author has been advised of the possibility of such damages.
