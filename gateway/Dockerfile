FROM  ubuntu:latest
RUN apt-get update \
 && apt-get install wget unzip zip -y
RUN apt-get install -y libxtst6 openjdk-11-jre uuid-runtime dbus wget
RUN wget https://download2.interactivebrokers.com/installers/ibgateway/stable-standalone/ibgateway-stable-standalone-linux-x64.sh
RUN chmod u+x ./ibgateway-stable-standalone-linux-x64.sh
# Generating a universally unique ID for the Container
RUN dbus-uuidgen > /etc/machine-id

# additional part to eliminate manual installation of IBKR Gateway:
# we turn off grafics rendering, so the only possible way to interact is through console,
# so we agree to install the Gateway with default settings and then turn on grafics to authorize
# in Gateway window
RUN unset DISPLAY
RUN echo '\n' | ./ibgateway-stable-standalone-linux-x64.sh --assume-yes
WORKDIR "/root/Jts/ibgateway/1012"
CMD ./ibgateway
