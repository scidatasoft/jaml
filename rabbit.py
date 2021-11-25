import json
from typing import List, Callable

import pika


class RabbitMQ:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.queues = []

    def publish(self, queue, payload):
        """Publish an arbitrary payload (json-izable)"""

        if queue not in self.queues:
            self.channel.queue_declare(queue=queue, durable=True)
            self.queues.append(queue)

        message = json.dumps(payload)
        self.channel.basic_publish(exchange='', routing_key=queue, body=message,
                                   properties=pika.BasicProperties(
                                       delivery_mode=2,  # make message persistent
                                   ))
        print(f" [x] Sent {message}")

    def __enter__(self):
        if self.connection is None:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                                credentials=pika.PlainCredentials(
                                                                                    username=self.username,
                                                                                    password=self.password)))
        if self.channel is None:
            self.channel = self.connection.channel()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

    def consume(self, queues: List[str], callback: Callable):
        """Prepare RabbitMQ stuff and start listening on specifying queues"""

        if self.channel is None:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host,
                                          credentials=pika.PlainCredentials(username=self.username,
                                                                            password=self.password),
                                          heartbeat=0))
            self.channel = connection.channel()

        self.channel.basic_qos(prefetch_count=1)

        print(f" [*] Consuming on", end=" ", flush=True)

        for queue in queues:
            print(f"'{queue}'", end=" ", flush=True)
            self.channel.queue_declare(queue=queue, durable=True)
            self.channel.basic_consume(queue=queue, on_message_callback=callback)

        # "management" queue must be declared in any case
        if "management" not in queues:
            self.channel.queue_declare(queue="management", durable=True)

        print("...")

        self.channel.start_consuming()

    @staticmethod
    def send_message(channel, queue, payload):
        """Publish a single message to already opened channel"""

        try:
            message = json.dumps(payload)
        except TypeError:
            message = json.dumps(payload.__dict__)

        channel.basic_publish(exchange='', routing_key=queue, body=message,
                              properties=pika.BasicProperties(
                                  delivery_mode=2,  # make message persistent
                              ))
