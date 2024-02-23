FROM ubuntu
# Chrome dependency Instalation
COPY . .
RUN apt update 
RUN apt-get install -y wget
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb

RUN apt install python3 -y
RUN apt install python3-pip -y
RUN pip install -r requirements.txt
ENTRYPOINT [ "python3", "main.py" ]