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
ARG ICLI_IBKR_ACCOUNT_ID
ENV ICLI_IBKR_ACCOUNT_ID=${ICLI_IBKR_ACCOUNT_ID}
ARG ICLI_IBKR_HOST
ENV ICLI_IBKR_HOST=${ICLI_IBKR_HOST}
ARG ICLI_IBKR_PORT
ENV ICLI_IBKR_PORT=${ICLI_IBKR_PORT}
RUN echo ${ICLI_IBKR_ACCOUNT_ID}
RUN echo ${ICLI_IBKR_HOST}
RUN echo ${ICLI_IBKR_PORT}
RUN echo "ICLI_IBKR_ACCOUNT_ID=${ICLI_IBKR_ACCOUNT_ID}\nICLI_IBKR_HOST=${ICLI_IBKR_HOST}\nICLI_IBKR_PORT=${ICLI_IBKR_PORT}\nICLI_REFRESH=3.3" >> .env.icli
