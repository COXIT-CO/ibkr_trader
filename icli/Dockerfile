FROM python:3  

WORKDIR /app

ENTRYPOINT ["tail", "-f", "/dev/null"]
COPY requirements.txt remove_pygame.py ./
RUN apt-get update -y
RUN apt-get install -y apt-utils python3-venv
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools supertools
RUN pip install ez_setup 
RUN apt-get install --assume-yes build-essential libcap-dev git 

RUN pip install -r requirements.txt
RUN git clone https://github.com/mattsta/icli.git
RUN mv icli icli2
RUN cp -r icli2/* .
RUN rm -rf icli2
RUN python remove_pygame.py
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
