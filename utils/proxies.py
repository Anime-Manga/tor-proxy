### DOCKER ###
import docker

### CONSTANTS ###
# Docker Settings
DOCKER_PROXY_IMAGE = "dockage/tor-privoxy:latest"

### NASTY GLOBAL VARIABLES (AT LEAST THEY ARE GLOBAL ONLY ON THIS MODULE) ###
# Declaring container map
docker_conatiner_map = {}
docker_container_list = []


# Gets the docker client
def get_docker_client():
    return docker.from_env()


# Initiation function to initialize all proxies
def initiate_proxies(replicas: int, start_port: int, expected_address: str):
    """
    # initiate_proxies()
    ## Function that initializes all proxies managed by the service
    :rerplicas: number of proxies (containers) that need to be started
    :start_port: start port of the proxies (all generated proxies will have a port equal to start_port + proxy number
    :expected_address: address expected from the requests
    """

    try:
        print(f"Intitiating '{replicas}' [{start_port} - {start_port + (replicas - 1)}] proxies ...")

        # Loop <replicas> times to create all proxies
        for replica_num in range(replicas):
            # Calculate the proxy container port that needs to be assigned
            container_port = start_port + replica_num
            # Format the container name
            container_name = f"animemanga-tor-proxy-{container_port}"
            # Construct the container address (used by the incoming messages to identify the proxy they need to manage)
            container_full_address = f"http://{expected_address}:{container_port}"

            print(f"Intitiating '{container_full_address}'")

            # Start the proxies and save their handles
            docker_conatiner_map[container_full_address] = get_docker_client().containers.run(image=DOCKER_PROXY_IMAGE, detach=True, ports={8118: container_port}, name=container_name)
            docker_container_list.append(container_full_address)  # Add the container to the <docker_container_list> (to generate the proxy.txt file and turn them off)

        print("All proxies are up and running!")
    except Exception as e:
        # Raise and exception appending the original error
        raise Exception(f"Cannot initiate '{DOCKER_PROXY_IMAGE}' please check your Docker configuration: " + str(e))


# Restart function to restart a specific proxy
def restart_proxy(proxy: str):
    """
    # restart_proxy
    ## Function that restarts a proxy given it's address
    :proxy: Full expected address of the proxy http://<address>:<port>
    :return bool: True: the proxy server has been found and restarted - False: the proxy server does not exists
    :raise Exception: if an unexpected error occurs
    """

    try:
        # Get proxy from the map
        proxy_container = docker_conatiner_map.get(proxy)

        # Check if the proxy exists
        if proxy_container:
            # If I get here, it exists and I can restart the proxy server
            proxy_container.restart()
            return True
        else:
            # If I get here, it does not exists so I'll do nothing
            return False
    except Exception as e:
        raise Exception(f"restart_proxy(): " + str(e))


# Termination function for all proxies
def terminate_proxies():
    try:
        print("Terminating proxies ...")

        # Turn off all of the containers for the proxies
        for container in docker_container_list:
            print(f"Terminating '{container}'")

            # Stopping container
            docker_conatiner_map[container].stop()
            # Removing container
            docker_conatiner_map[container].remove()

        print("Proxies terminated!")
    except Exception as e:
        # Raise and exception appending the original error
        raise Exception("An error occurred while terminating and removing proxies, please remove any remaining proxies manually and Check docker your configuration: " + str(e))
