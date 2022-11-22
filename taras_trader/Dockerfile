FROM python:3  

WORKDIR /app

ENTRYPOINT ["tail", "-f", "/dev/null"]
COPY . .
RUN apt-get update -y
RUN apt-get install -y apt-utils python3-venv python3-pip
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools supertools
RUN pip install ez_setup 

RUN apt-get install --assume-yes build-essential libcap-dev git 
RUN pip install -r requirements.txt
WORKDIR "/app"
RUN touch .env.icli
RUN echo 'ICLI_IBKR_ACCOUNT_ID="DU1820017"\nICLI_IBKR_HOST="10.5.0.5"\nICLI_IBKR_PORT=4002\nICLI_REFRESH=3.3' >> .env.icli
