### RABBITMQ ###
import pika
from pika.exceptions import AMQPConnectionError

### NASTY GLOBAL VARIABLES (AT LEAST THEY ARE GLOBAL ONLY ON THIS MODULE) ###
# Declaring connection and channel
connection = None
channel = None


# Connects to the RabbitMQ server
def connect(host: str, port: int, user: str, passwd: str):
    # In order for the function to see the connection and channel variables
    global connection
    global channel

    try:
        # Establish a connection to RabbitMQ server
        print(f"Connecting to rabbitmq://{host}:{port} ...")

        # Setup of plain credentials
        credentials = pika.PlainCredentials(username=user, password=passwd)

        # Setup connection parameters
        parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=credentials,
            connection_attempts=10, # Number of retry attempts if connection fails
            retry_delay=5,          # Delay in seconds between connection retries
            socket_timeout=10,      # Socket operation timeout in seconds
        )

        # Setup of the connection
        connection = pika.BlockingConnection(parameters=parameters)
        # Connecting to the RabbitMQ service
        channel = connection.channel()

        print(f"Connection to rabbitmq://{host}:{port} estabished!")
    except AMQPConnectionError:
        # Raise and exception
        raise Exception("Can't connect to RabbitMQ (check ip/hostname:port or that credentials are correct)")


# Declares an exchange
def exchenage_declare(exchange_name: str, type: str = 'fanout', durable: bool = False):
    # Declare the exchange
    channel.exchange_declare(exchange=exchange_name, exchange_type=type, durable=durable)


# Declares a queue
def queue_declare(queue_name: str):
    # Declaring the message queue
    channel.queue_declare(queue=queue_name)
    # print(f"Delcared 'rabbitmq://{args.rabbit_host}:{args.rabbit_port}/{args.queue_name}'")
    print(f"Delcared queue '{queue_name}'")


#  Bind queue to exchange
def bind_queue(exchange_name: str, queue_name: str):
    channel.queue_bind(exchange=exchange_name, queue=queue_name)


# Declare how the messages will be handled by the consumer
def basic_consume(queue: str, on_message_callback, auto_ack: bool):
    channel.basic_consume(queue=queue, on_message_callback=on_message_callback, auto_ack=auto_ack)


# Start consuming messages
def start_consuming():
    print('Waiting for messages. To exit, press CTRL+C')
    channel.start_consuming()


# Close the rabbitmq connection
def close_connection():
    try:
        # Closing the RabbitMQ connection
        print('Closing RabbitMQ connection ...')
        connection.close()
    except Exception as e:
        raise Exception("There was and error while closing the connection from RabbitMQ: " + str(e))
