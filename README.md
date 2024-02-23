# GetGrass Docker Image

An unofficial Docker Image for getgrass.io. GetGrass allows you to earn passive income by sharing your network bandwidth.

## Getting Started

1. **Clone the Repository**:
   - First, clone the files from this repository to your local device:

     ```bash
     git clone https://github.com/kgregor98/grass.git
     cd grass
     ```

2. **Build the Docker Image**:
   - Navigate to the folder where the cloned files are located.
   - Build the Docker image using the following command:

     ```docker build -t grass .```

3. **Run the Docker Container**:
   - Now you can run the Docker container with the appropriate environment variables.
   - Replace `<your_email>` and `<your_password>` with your actual Grass account credentials:

     ```docker run -d -e USER=<your_email> -e PASS=<your_password> grass```





## License

This program is free software distributed under the terms of the GNU General Public License (GPL-3.0). You can redistribute it and/or modify it under the terms of the license. However, there is no warranty provided, and you use it at your own risk.
