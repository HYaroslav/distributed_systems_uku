# Distributed systems UKU

## Configuration
There is a configuration file called `dev.env` with the following variables:
- MASTER_PORT -- port on which master node will listen
- SECONDARY_START_PORT -- the port of the first secondary node. Ports of all next secondary nodes will be increased incrementally by one.
- SECONDARY_NUMBER -- amount of secondary nodes.

## Launching
To run the app, you can simply run `./run.sh` bash script. It will generate `docker-compose` in memory and run it.
As a result you will get one master container and `SECONDARY_NUMBER` secondary containers.
