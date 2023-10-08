import os
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
# ArgumentParser Defaults
DEF_RABBIT_HOST = os.environ.get('ADDRESS_RABBIT', "localhost")
DEF_RABBIT_PORT = os.environ.get('PORT_RABBIT', 5672)
DEF_RABBIT_USER = os.environ.get('USERNAME_RABBIT', "guest")
DEF_RABBIT_PASS = os.environ.get('PASSWORD_RABBIT', "guest")
DEF_RABBIT_EXCH = os.environ.get('EXCHANGE_NAME', "")
DEF_RABBIT_QUEUE = os.environ.get('QUEUE_RABBIT', "animemanga-tor-proxy")
DEF_PROXY_REPLICAS = os.environ.get('REPLICAS', 15)
DEF_EXPECTED_ADDR = os.environ.get('EXPECTED_ADDRESS', DEF_RABBIT_HOST)
DEF_START_PORT = os.environ.get('START_PORT', 8000)
DEF_PROXY_PATH = os.environ.get('PROXY_PATH', "proxy.txt")


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


# Register the signal handler for SIGINT and SIGTERM (CTLR+C and unexpected interrupts)
signal.signal(signal.SIGINT, handle_termination)
signal.signal(signal.SIGTERM, handle_termination)


# Callback called when messages come in from the queue
def callback(ch, method, properties, body):
    # Parse the message into a Json object
    json_object = json.loads(body.decode('UTF-8'))['message']
    print(f"Received payload: {json_object}")

    # Go trought all possible actions
    if(json_object['action'] == "restart"):  # Action: restart
        # Restart proxy
        if(proxies.restart_proxy(json_object['endpoint'])):
            print(f"Proxy '{json_object['endpoint']}' restarted ...")

            # Manually acknowledge (ack) the message (the proxy has been restarted succesfully)
            ch.basic_ack(delivery_tag=method.delivery_tag)


### ENTRY POINT ###
def main():
    parser = ArgumentParser(PRG_NAME, description=PRG_DESC, epilog=PRG_EPIL)
    parser.add_argument('--rabbit-host', default=DEF_RABBIT_HOST, help="ip/hostname of the RabbitMQ service")
    parser.add_argument('--rabbit-port', default=DEF_RABBIT_PORT, help="port of the RabbitMQ service [default: 5672]")
    parser.add_argument('--rabbit-user', default=DEF_RABBIT_USER, help="username of the RabbitMQ service")
    parser.add_argument('--rabbit-pass', default=DEF_RABBIT_PASS, help="password of the RabbitMQ service")
    parser.add_argument('--exchange-name', default=DEF_RABBIT_EXCH, help="name of the exchange that needs to be created")
    parser.add_argument('--queue-name', default=DEF_RABBIT_QUEUE, help="name of the message queue that needs to be created")
    parser.add_argument('--replicas', default=DEF_PROXY_REPLICAS, type=int, help="the amount of proxy containers that need to be created")
    parser.add_argument('--expected-address', default=DEF_EXPECTED_ADDR, help="expected IP address from the message-queue (incoming messages address proxies using 'http://<expected-address>:<proxy_port>')")
    parser.add_argument('--start-port', default=DEF_START_PORT, type=int, help="the starting port the assign to the proxies (every proxy will have assigned a port number +1 of the previews)")
    parser.add_argument('--proxy-file', default=DEF_PROXY_PATH, help="full path to the proxy file to be written")
    args = parser.parse_args()

    try:
        # Initialize proxies
        proxies.initiate_proxies(args.replicas, args.start_port, args.expected_address)

        # Write the proxy file at the path specified
        proxies.write_proxy_file(args.proxy_file)

        # Connecto to RabbitMQ
        rabbitmq.connect(host=args.rabbit_host, port=args.rabbit_port, user=args.rabbit_user, passwd=args.rabbit_pass)

        # Declare the exchange and queue that we are going to listen
        rabbitmq.exchenage_declare(exchange_name=args.exchange_name, durable=True)
        rabbitmq.queue_declare(queue_name=args.queue_name)

        # Binsing queue to exchange
        rabbitmq.bind_queue(exchange_name=args.exchange_name, queue_name=args.queue_name)

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
