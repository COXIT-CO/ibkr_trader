FROM python:3

WORKDIR /app

COPY . .
RUN apt-get update -y
RUN apt-get install -y apt-utils python3.9 python3-venv python3-pip
RUN pip install --upgrade pip
RUN python -m pip install -U pip
RUN pip install --upgrade setuptools supertools
RUN pip install ez_setup 

RUN apt-get install --assume-yes build-essential libcap-dev
RUN git clone http://github.com/seveas/python-prctl || \
    cd python-prctl || \
    python setup.py build || \
    sudo python setup.py install
RUN git clone https://github.com/pygame/pygame.git || \
    cd pygame || \
    python setup.py build || \
    sudo python setup.py install
RUN pip install -r requirements.txt
ENTRYPOINT ["tail", "-f", "/dev/null"]
# RUN python -m icli
