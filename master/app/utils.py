
SECONDARY_LISTENER_ADDRESS = "172.20.0.{host_address}:{port}"
SECONDARY_LOCAL_ADDRESS = "http://localhost:{port}"

def get_secondaries_ip_list(secondaries_number: int, start_port: int):
    secondary_endpoints_list = []
    for i in range(secondaries_number):
        # IPv4 for secondaries will start from 172.20.0.3
        endpoint = SECONDARY_LISTENER_ADDRESS.format(host_address=i+3, port=start_port+i)
        secondary_endpoints_list.append(endpoint)

    return secondary_endpoints_list

def get_secondaries_listener_ip_list(secondaries_number: int, start_port: int):
    secondary_endpoints_list = []
    for i in range(secondaries_number):
        # IPv4 for secondaries will start from 172.20.0.3
        # Port of listener will be SECONDARY_PORT+1
        endpoint = SECONDARY_LISTENER_ADDRESS.format(host_address=i+3, port=start_port+i+1)
        secondary_endpoints_list.append(endpoint)

    return secondary_endpoints_list

def get_secondaries_local_ip_list(secondaries_number: int, start_port: int):
    secondary_endpoints_list = []
    for i in range(secondaries_number):
        endpoint = SECONDARY_LOCAL_ADDRESS.format(port=start_port+i)
        secondary_endpoints_list.append(endpoint)

    return secondary_endpoints_list
