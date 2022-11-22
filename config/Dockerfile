FROM ubuntu:latest

ENTRYPOINT ["tail", "-f", "/dev/null"]
COPY . .
RUN apt-get update
RUN apt-get install -y nano
