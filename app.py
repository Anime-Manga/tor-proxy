import sys
import json
import signal
from argparse import ArgumentParser

### UTILS ###
from utils import proxies
from utils import rabbitmq

### CONSTANTS ###
# ArgumentParser Settings
PRG_NAME = "animemanga-tor-privoxy"
PRG_DESC = "Anime Manga - tor-privoxy container manager"
PRG_EPIL = f"V1 - {PRG_NAME}"


### FUNCTIONS ###
# Define a function to handle termination signals
def handle_termination(signal, frame):
    print("Closing gracefully, please wait ...")

    # Terminate all started proxies (if any)
    proxies.terminate_proxies()
    # Close connection with RabbitMQ
    rabbitmq.close_connection()

    # Exit with OK
    sys.exit(0)


# Register the signal handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, handle_termination)
signal.signal(signal.SIGTERM, handle_termination)


# Callback called when messages come in from the queue
def callback(ch, method, properties, body):
    # Parse the message into a Json object
    json_object = json.loads(body.decode('UTF-8'))

    # Go trought all possible actions
    if(json_object['action'] == "restart"):  # Action: restart
        print(f"Restarting proxy '{json_object['proxy']}' ...")

        # Restart proxy
        proxies.restart_proxy(json_object['proxy'])
        # Manually acknowledge (ack) the message
        #ch.basic_ack(delivery_tag=method.delivery_tag)

        print(f"Proxy '{json_object['proxy']}' restarted ...")


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

    try:
        # Initialize proxies
        proxies.initiate_proxies(args.replicas, args.start_port, args.expected_address)

        # Opening and reading the creds file for the RabbitMQ connection
        creds = []
        with open(args.creds, 'r') as creds_file:
            # Replacing line terminations with nothing, so they can get the f*** out of here
            creds = [cred.replace("\n", "") for cred in creds_file.readlines()]

        # Connecto to RabbitMQ
        rabbitmq.connect(host=args.rabbit_host, port=args.rabbit_port, user=creds[0], passwd=creds[1])

        # Delcare the queue that we are going to listen
        rabbitmq.declare(args.queue_name)

        # Declare the method of consumption
        rabbitmq.basic_consume(queue=args.queue_name, on_message_callback=callback, auto_ack=False)

        # Start consuming messages
        rabbitmq.start_consuming()
    except Exception as e:
        # Print the error in the console
        print(e)

        # Terminate all started proxies (if any)
        proxies.terminate_proxies()
        # Close connection with RabbitMQ
        rabbitmq.close_connection()

        # Exit with error
        sys.exit(-1)


if __name__ == "__main__":
    main()
