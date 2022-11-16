FROM --platform=linux/amd64 ubuntu:latest
RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository -y universe
RUN apt-get update
RUN apt-get install -y x11vnc \
    xvfb \
    autocutsel \
    xfce4-clipman \
    wget \
    unzip \
    zip \
    libxtst6 \
    openjdk-11-jre \
    uuid-runtime \
    dbus
RUN wget https://download2.interactivebrokers.com/installers/ibgateway/stable-standalone/ibgateway-stable-standalone-linux-x64.sh
RUN chmod u+x ./ibgateway-stable-standalone-linux-x64.sh

# additional part to eliminate manual installation of IBKR Gateway:
# we turn off grafics rendering, so the only possible way to interact is through console,
# so we agree to install the Gateway with default settings and then turn on grafics to authorize
# in Gateway window
RUN unset DISPLAY
RUN echo '\n' | ./ibgateway-stable-standalone-linux-x64.sh --assume-yes
WORKDIR "/root/Jts/ibgateway/1019"
RUN echo "exec ./ibgateway" > ~/.xinitrc && chmod +x ~/.xinitrc
CMD ["x11vnc", "-create", "-forever", "-clip", "1100x850+230+200"]
