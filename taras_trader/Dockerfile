FROM python:3

WORKDIR /app

COPY . .
RUN apt-get update -y
# RUN apt-get install -y apt-utils
RUN apt-get update && apt-get install --assume-yes apt-utils
RUN apt-get install -y python3.9
RUN apt-get install -y python3-venv python3-pip
RUN pip install --upgrade pip
RUN python -m pip install -U pip
RUN pip install --upgrade setuptools supertools
RUN pip install ez_setup 
# RUN pip install python-prctl
# RUN apt-get install -y pip3.9
# RUN apt-get install -y libpcap-dev libcap2 libcap-ng-dev libcap-ng-utils libcap2-bin libcapnp-dev
RUN apt-get install --assume-yes gcc build-essential libcap-dev
RUN git clone http://github.com/seveas/python-prctl || \
    cd python-prctl || \
    python setup.py build || \
    sudo python setup.py install
RUN git clone https://github.com/pygame/pygame.git || \
    cd pygame || \
    python setup.py build || \
    sudo python setup.py install
RUN pip install -r requirements.txt
RUN ls

# RUN python -m icli