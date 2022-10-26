#!/bin/sh

set -a
. ./dev.env
set +a

SECONDARY_REPLICAS_NUMBER=$(($SECONDARY_NUMBER-1))

buildComposeYaml() {
  cat <<HEADER
version: '3'
services:
HEADER
    cat <<BLOCK
  master:
    build: ./master
    image: master_image
    env_file:
      - ./dev.env
    ports:
      - "$MASTER_PORT:$MASTER_PORT"
    environment:
      - PORT=$MASTER_PORT
    networks:
      distributed_system:
        ipv4_address: 172.20.0.2
  secondary_0:
    build: ./secondary
    image: secondary_image
    depends_on: [master]
    env_file:
      - ./dev.env
    ports:
      - "$SECONDARY_START_PORT:$SECONDARY_START_PORT"
    environment:
      - LISTENER_IP=172.20.0.3
      - PORT=$(($SECONDARY_START_PORT))
    networks:
      distributed_system:
        ipv4_address: 172.20.0.3
BLOCK
  for i in $(seq $SECONDARY_REPLICAS_NUMBER); do
    cat <<BLOCK 
  secondary_$i:
    image: secondary_image
    depends_on: [secondary_$(($i-1))]
    env_file:
      - ./dev.env
    ports:
      - "$(($SECONDARY_START_PORT+$i)):$(($SECONDARY_START_PORT+$i))"
    environment:
      - LISTENER_IP=172.20.0.$(($i+3))
      - PORT=$(($SECONDARY_START_PORT+$i))
    networks:
      distributed_system:
        ipv4_address: 172.20.0.$(($i+3))
BLOCK
  done
cat<<BLOCK
networks:
  distributed_system:
    name: distributed_system_network
    ipam:
      config:
        - subnet: 172.20.0.0/16
BLOCK
}


if [[ "$1" == "--build" ]]
then
    buildComposeYaml | docker-compose -f- build
    buildComposeYaml | docker-compose -f- up --remove-orphans
else
    buildComposeYaml | docker-compose -f- up
fi