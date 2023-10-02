import sys
import json
import signal
from argparse import ArgumentParser

### DOCKER ###
import docker

### RABBITMQ ###
import pika
from pika.exceptions import AMQPConnectionError


### CONSTANTS ###
# ArgumentParser Settings
PRG_NAME = "animemanga-tor-privoxy"
PRG_DESC = "Anime Manga - tor-privoxy container manager"
PRG_EPIL = f"V1 - {PRG_NAME}"
# Docker Settings
DOCKER_PROXY_IMAGE = "dockage/tor-privoxy:latest"


### NASTY GLOBAL VARIABLES ###
# Declaring container map
docker_conatiner_map = {}
docker_container_list = []


### FUNCTIONS ###
# Termination function for all started proxies
def terminate_proxies():
    try:
        # Turn off all of the containers for the proxies
        for container in docker_container_list:
            docker_conatiner_map[container].stop()
            docker_conatiner_map[container].remove()
    except Exception as e:
        print("An error occurred while stopping and removing proxies, please remove them manually and check your Docker configuration")
        print(e)
        sys.exit(-1)


# Define a function to handle termination signals
def handle_termination(signal, frame):
    print("Closing gracefully, please wait ...")
    terminate_proxies()
    sys.exit(0)


# Register the signal handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, handle_termination)
signal.signal(signal.SIGTERM, handle_termination)


### ENTRY POINT ###
def main():
    parser = ArgumentParser(PRG_NAME, description=PRG_DESC, epilog=PRG_EPIL)
    parser.add_argument('--rabbit-host', required=True, help="ip/hostname of the RabbitMQ service")
    parser.add_argument('--rabbit-port', default=5672, help="port of the RabbitMQ service [default: 5672]")
    parser.add_argument('--creds', default='creds', help="path to a file containing the credentials needed to connect to RabbitMQ")
    parser.add_argument('--queue-name', default='animemanga-tor-proxy', help="name of the message queue that needs to be created")
    parser.add_argument('--replicas', default=15, help="the amount of proxy containers that need to be created")
    parser.add_argument('--expected-address', required=True, help="expected IP address from the message-queue (incoming messages address proxies using 'http://<expected-address>:<proxy_port>')")
    parser.add_argument('--start-port', default=8000, type=int, help="the starting port the assign to the proxies (every proxy will have assigned a port number +1 of the previews)")
    args = parser.parse_args()

    # Getting Docker client instance to control the Docker installation
    docker_client = docker.from_env()

    try:
        print(f"Starting '{args.replicas}' [{args.start_port}-{args.start_port + (args.replicas - 1)}] proxies ...")

        # Loop <args.replicas> times to create all proxies
        for proxy in range(args.replicas):
            # Calculate the proxy container port that needs to be assigned
            container_port = args.start_port + proxy
            # Format the container name
            container_name = f"animemanga-tor-proxy-{container_port}"
            # Construct the container address (used by the incoming messages to identify the proxy they need to address)
            container_full_address = f"http://{args.expected_address}:{container_port}"

            # Start the proxies and save their handles
            docker_conatiner_map[container_full_address] = docker_client.containers.run(image=DOCKER_PROXY_IMAGE, detach=True, ports={8118: container_port}, name=container_name)
            docker_container_list.append(container_full_address)  # Add the container to the <docker_container_list> (to generate the proxy.txt file and turn them off)

        print("All proxies are up and running!")
    except Exception as e:
        print(f"Can't run '{DOCKER_PROXY_IMAGE}' please check your Docker configuration")
        print(e)
        sys.exit(-1)

    # Opening and reading the creds file
    creds = []
    with open(args.creds, 'r') as creds_file:
        # Replacing line terminations with nothing, so they can get the f*** out of here
        creds = [cred.replace("\n", "") for cred in creds_file.readlines()]

    try:
        # Establish a connection to RabbitMQ server
        print(f"Connecting to rabbitmq://{args.rabbit_host}:{args.rabbit_port} ...")

        # Setup of plain credentials
        credentials = pika.PlainCredentials(username=creds[0], password=creds[1])
        # Setup of the connection
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=args.rabbit_host, port=args.rabbit_port, credentials=credentials))
        # Connecting to the RabbitMQ service
        channel = connection.channel()

        print(f"Connection to rabbitmq://{args.rabbit_host}:{args.rabbit_port} estabished!")
    except AMQPConnectionError:
        print("Can't connect to RabbitMQ (check ip/hostname:port or that credentials are correct)")
        sys.exit(-1)

    # Declaring the message queue
    channel.queue_declare(queue=args.queue_name)
    print(f"Delcared 'rabbitmq://{args.rabbit_host}:{args.rabbit_port}/{args.queue_name}'")

    # Callback called when messages come in from the queue
    def callback(ch, method, properties, body):
        # Parse the message into a Json object
        json_object = json.loads(body.decode('UTF-8'))

        # Go trought all possible actions
        if(json_object['action'] == "restart"):  # Action: restart
            print(f"Restarting proxy '{json_object['proxy']}' ...")
            # Restart proxy from the map
            docker_conatiner_map[json_object['proxy']].restart()
            # Manually acknowledge (ack) the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"Proxy '{json_object['proxy']}' restarted ...")

    # Declare how the messages will be handled by the consumer
    channel.basic_consume(queue=args.queue_name, on_message_callback=callback, auto_ack=False)

    try:
        # Start consuming messages
        print('Waiting for messages. To exit, press CTRL+C')
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Closing gracefully, please wait ...")

        # Close the connection to the RabbitMQ service
        connection.close()
        # Call the temrination function for all proxies
        terminate_proxies()

        # At this point evrything is correctly closed
        sys.exit(0)


if __name__ == "__main__":
    main()
