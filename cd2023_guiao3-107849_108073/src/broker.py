"""Message Broker"""
import enum
import socket
import selectors
import json
import pickle
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple
from src.log import get_logger
from src.protocol import Protocol

class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2


class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""
        self.canceled = False
        self._host = "localhost"
        self._port = 5000
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((self._host, self._port))
        self._socket.listen()
        self._socket.setblocking(False)
        self._selector = selectors.DefaultSelector()
        self._selector.register(self._socket, selectors.EVENT_READ, self._accept)
        self._logger = get_logger("Broker")

        self._topics: Dict[str, Any] = {}
        self._subscriptions: Dict[str, List[Tuple[socket.socket, Serializer]]] = {}

    def list_topics(self) -> List[str]:
        """Returns a list of strings containing all topics containing values."""
        return [topic for topic in self._topics if self._topics[topic]]

    def get_topic(self, topic):
        """Returns the currently stored value in topic."""
        if topic not in self._topics:
            return None
        if not self._topics[topic]:
            return None
        return self._topics[topic]

    def put_topic(self, topic, value):
        """Store in topic the value."""
        if topic not in self._topics:
            self._create_topic(topic)
        self._topics[topic] = value
        self._notify(topic)

    def list_subscriptions(self, topic: str) -> List[Tuple[socket.socket, Serializer]]:
        """Provide list of subscribers to a given topic."""
        return self._subscriptions[topic]

    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        """Subscribe to topic by client in address."""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        self._subscriptions[topic].append((address, _format))

    def unsubscribe(self, topic, address):
        """Unsubscribe to topic by client in address."""
        if topic not in self._subscriptions:
            return
        self._subscriptions[topic] = [
            sub for sub in self._subscriptions[topic] if sub[0] != address
        ]

    def _notify(self, topic):
        """Notify subscribers of topic."""
        subscribers = []
        original_topic = topic
        values = self._topics[topic]
        self._logger.info(f"Values = {values}")
        self._logger.info(f"Topic = {topic}")
        if "/" in topic:
            while "/" in topic:
                subscribers += self._subscriptions[topic]
                topic = topic[: topic.rfind("/")]
        else:
            subscribers += self._subscriptions[topic]
        for subscriber in subscribers:

            self._logger.info(f"Notifying subscriber {subscriber[0]}:{subscriber[1]}")
            Protocol.send(Protocol.notify(original_topic, values), subscriber[0], subscriber[1])
    
    def _create_topic(self, topic):
        """Create a new topic."""
        if topic in self._topics:
            return
        self._topics[topic] = None
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []

    def _accept(self, sock, mask):
        """Accept new connection."""
        self._logger.info("Accepting new connection")
        conn, addr = sock.accept()
        conn.setblocking(False)
        self._selector.register(conn, selectors.EVENT_READ, self._read)

    def run(self):
        """Run until canceled."""

        while not self.canceled:
            events = self._selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
            

    def _read(self, conn, mask):
        """Read data from connection."""
        rec_msg = Protocol.recv(conn)
        self._logger.debug(f"Received message {rec_msg}")
        if not rec_msg:
            self.close_connection(conn)
            return

        msg_type = rec_msg.type
        self._logger.debug(f"Received message of type {msg_type}")
        self._logger.debug(f"Received message {rec_msg}")

        if msg_type == "req_topics":
            topics = self.list_topics()
            Protocol.send(conn, Protocol.rep_topics(topics), rec_msg.serializer)
        
        rec_args = rec_msg.args
        self._logger.info(f"Received message with args {rec_args}")

        if msg_type == "subscribe":
            self.subscribe(rec_args["topic"], conn, rec_args["serializer"])
            self._logger.info(f"Subscribed {conn} to {rec_args['topic']}")

        elif msg_type == "unsubscribe":
            self.unsubscribe(rec_args["topic"], conn)
            self._logger.info(f"Unsubscribed {conn} from {rec_args['topic']}")

        elif msg_type == "create_topic":
            self._create_topic(rec_args["topic"])
            self._logger.info(f"Created topic {rec_args['topic']}")

        elif msg_type == "publish":
            self.put_topic(rec_args["topic"], rec_args["data"])
            self._logger.info(f"Published {rec_args['data']} to {rec_args['topic']}")

        else:
            self._logger.info(f"Received message with invalid type {rec_msg}")
            return
    
    def close_connection(self, conn):
        """Close connection."""
        self._logger.info(f"Closing connection {conn}")
        topics = self.list_topics()
        for topic in topics:
            self.unsubscribe(topic, conn)
        self._selector.unregister(conn)
        conn.close()
        return


