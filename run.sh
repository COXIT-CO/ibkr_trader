#!/bin/sh

git clone https://github.com/UnusualAlpha/ib-gateway-docker.git
find ./ib-gateway-docker -mindepth 1 ! -regex '^./ib-gateway-docker/latest\(/.*\)?' -delete
cd ./taras_trader/taras_trader
rm config.yaml
touch config.yaml
cd ../../scrape_server
rm config.yaml
touch config.yaml
cd ..
rm config.yaml
touch config.yaml
docker compose build --no-cache
docker compose up