import sys
import json
import signal
from argparse import ArgumentParser

### RABBITMQ ###
import pika
from pika.exceptions import AMQPConnectionError

### UTILS ###
from utils import proxies


### CONSTANTS ###
# ArgumentParser Settings
PRG_NAME = "animemanga-tor-privoxy"
PRG_DESC = "Anime Manga - tor-privoxy container manager"
PRG_EPIL = f"V1 - {PRG_NAME}"


### FUNCTIONS ###
# Define a function to handle termination signals
def handle_termination(signal, frame):
    print("Closing gracefully, please wait ...")
    proxies.terminate_proxies()
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

    try:
        # Initialize proxies
        proxies.initiate_proxies(args.replicas, args.start_port, args.expected_address)
    except Exception as e:
        # If an error occurs:
        #   Print the error
        #   Terminate all started proxies (if any)
        print(e)
        proxies.terminate_proxies()

        # Exit with error
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
        # If an error occurs:
        #   Print the error
        #   Terminate all started proxies (if any)
        print("Can't connect to RabbitMQ (check ip/hostname:port or that credentials are correct)")
        proxies.terminate_proxies()

        # Exit with error
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

            # Restart proxy
            proxies.restart_proxy(json_object['proxy'])
            # Manually acknowledge (ack) the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

            print(f"Proxy '{json_object['proxy']}' restarted ...")

    # Declare how the messages will be handled by the consumer
    channel.basic_consume(queue=args.queue_name, on_message_callback=callback, auto_ack=False)

    # Start consuming messages
    print('Waiting for messages. To exit, press CTRL+C')
    channel.start_consuming()


if __name__ == "__main__":
    main()
