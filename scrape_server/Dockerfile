FROM python:3  

WORKDIR /app

COPY . .
RUN apt-get update -y
RUN apt-get install -y apt-utils python3-venv
RUN pip install --upgrade pip

RUN apt-get install --assume-yes curl
RUN pip install -r requirements.txt
CMD python -m src
