# Distributed systems UKU

## Configuration
There is a configuration file called `dev.env` with the following variables:
- MASTER_PORT - port on which master node will listen
- SECONDARY_START_PORT - the port of the first secondary node. Ports of all next secondary nodes will be increased incrementally by one.
- SECONDARY_NUMBER - amount of secondary nodes.

## Launching
To build and run the app, you can simply run `./run.sh --build` command. Bash script will generate `docker-compose` in memory and run it.
As a result you will get one master container and `SECONDARY_NUMBER` secondary containers.

If you will not change the `dev.env` parameters then the addresses of nodes will be as follow:
 - master - `http://localhost:8080`
 - secondary_1 - `http://localhost:8081`
 - secondary_2 - `http://localhost:8082`
 - secondary_3 - `http://localhost:8083`

## Existing endpoints
Master node:
 - GET `/get_message` - get list of massages from local variable.
 - POST `/append_message` - append a massages to a local variable. The data should be passed in json.

Secondary nodes:
 - GET `/get_message` - get list of massages from local variable.