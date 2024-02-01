"""Middleware to communicate with PubSub Message Broker."""
from collections.abc import Callable
from enum import Enum
from queue import LifoQueue, Empty
from typing import Any
import socket
from src.log import get_logger
from src.broker import Serializer
import pickle
import xml.etree.ElementTree as ET
from src.protocol import Protocol
class MiddlewareType(Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2


class Queue:
    """Representation of Queue interface for both Consumers and Producers."""
    
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        self.topic = topic
        self.type = _type
        self.queue = LifoQueue()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 5000))
        self._logger = get_logger("Middleware")
        """Create Queue."""

    def push(self, value):
        """Sends data to broker."""
        self._logger.debug("Sending %s", Protocol.publish(self.topic, value))
        Protocol.send(Protocol.publish(self.topic, value), self.socket, self.serializer.value)
    
    def pull(self) -> (str, Any):
        """Receives (topic, data) from broker.

        Should BLOCK the consumer!"""
        pass
    
    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        self._logger.debug("Sending %s", Protocol.list_topics())
        Protocol.send(Protocol.list_topics(), self.socket, self.serializer.value)
        msg = Protocol.recv(self.socket)
        self._logger.debug("Received message: %s", msg)
        for topic in msg.args["topics"]:
            self._logger.debug(topic)
            print(topic)

        callback(msg.args["topics"])
        
    
    def cancel(self):
        """Cancel subscription."""
        self._logger.debug("Sending %s", Protocol.unsubscribe(self.topic))
        Protocol.send(Protocol.unsubscribe(self.topic), self.socket, self.serializer.value)
        pass

class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)
        self.serializer = Serializer.JSON    
        if _type == MiddlewareType.CONSUMER:
            self._logger.debug("Subscribing to topic %s", topic)
            self._logger.debug("Sending %s", Protocol.subscribe(topic, self.serializer.value))
            Protocol.send(Protocol.subscribe(topic, self.serializer.value), self.socket, self.serializer.value)
        elif _type == MiddlewareType.PRODUCER:
            self._logger.debug("Creating topic %s", topic)
            self._logger.debug("Sending %s", Protocol.create_topic(topic))
            Protocol.send(Protocol.create_topic(topic), self.socket, self.serializer.value)
        else:
            raise ValueError("Invalid Middleware Type.")

    def push(self, value):
        """Sends data to broker."""
        if self.type == MiddlewareType.CONSUMER:
            return
        self._logger.debug("Publishing to topic %s, value %s", self.topic, value)
        super().push(value)

    def pull(self) -> (str, Any):
        if self.type == MiddlewareType.PRODUCER:
            return
        if self.queue.empty():
            self._receive()
        self._logger.debug("Queue Size: %d", self.queue.qsize())
        return (self.topic,self.queue.get())

    def _receive(self):
        """Receives (topic, data) from broker.

        Should BLOCK the consumer!"""
        msg = Protocol.recv(self.socket)
        self._logger.debug("Received message1: %s", msg)
        self._logger.debug("Received message2: %s", msg.args)
        self._logger.debug("Received message3: %s", msg.args["data"])
        self.queue.put(msg.args["data"])

    def list_topics(self, callback: Callable):
        """dunno"""
        super().list_topics(callback)

    def cancel(self):
        """Cancel subscription."""
        if self.type == MiddlewareType.PRODUCER:
            return

        super().cancel(self.topic)

class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)
        self.serializer = Serializer.XML
        if _type == MiddlewareType.CONSUMER:
            self._logger.debug("Subscribing to topic %s", topic)
            self._logger.debug("Sending %s", Protocol.subscribe(topic, self.serializer.value))
            Protocol.send(Protocol.subscribe(topic, self.serializer.value), self.socket, self.serializer.value)
        elif _type == MiddlewareType.PRODUCER:
            self._logger.debug("Creating topic %s", topic)
            self._logger.debug("Sending %s", Protocol.create_topic(topic))
            Protocol.send(Protocol.create_topic(topic), self.socket, self.serializer.value)
        else:
            raise ValueError("Invalid MiddlewareType")

    def push(self, value):
        """Sends data to broker."""
        if self.type == MiddlewareType.CONSUMER:
            return
        self._logger.debug("Publishing to topic %s, value %s", self.topic, value)
        super().push(value)


    def pull(self) -> (str, Any):
        if self.type == MiddlewareType.PRODUCER:
            return
        if self.queue.empty():
            self._receive()
        self._logger.debug("Queue size: %d", self.queue.qsize())
        return (self.topic, self.queue.get())
    
    def _receive(self):
        """Receives (topic, data) from broker.

        Should BLOCK the consumer!"""
        msg = Protocol.recv(self.socket)
        self._logger.debug("Received message: %s", msg)
        self.queue.put(msg.args["data"])

    def list_topics(self, callback: Callable):
        """dunno"""
        super().list_topics(callback)

    def cancel(self):
        """Cancel subscription."""
        if self.type == MiddlewareType.PRODUCER:
            return
        super().cancel(self.topic)

class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)
        self.serializer = Serializer.PICKLE
        if _type == MiddlewareType.CONSUMER:
            self._logger.debug("Subscribing to topic %s", topic)
            self._logger.debug("Sending %s", Protocol.subscribe(topic, self.serializer.value))
            Protocol.send(Protocol.subscribe(topic, self.serializer.value), self.socket, self.serializer.value)
        elif _type == MiddlewareType.PRODUCER:
            self._logger.debug("Creating topic %s", topic)
            self._logger.debug("Sending %s", Protocol.create_topic(topic))
            Protocol.send(Protocol.create_topic(topic), self.socket, self.serializer.value)
        else:
            raise ValueError("Invalid type")

            
    def push(self, value):
        """Sends data to broker."""
        if self.type == MiddlewareType.CONSUMER:
            return
        self._logger.debug("Publishing to topic %s, value %s", self.topic, value)
        super().push(value)

    def pull(self) -> (str, Any):
        if self.type == MiddlewareType.PRODUCER:
            return
        if self.queue.empty():
            self._receive()
        self._logger.debug("Queue size: %d", self.queue.qsize())
        return (self.topic, self.queue.get())
    
    def _receive(self):
        """Receives (topic, data) from broker.

        Should BLOCK the consumer!"""
        msg = Protocol.recv(self.socket)
        self._logger.debug("Received message: %s", msg)
        self.queue.put(msg.args["data"])
    
    def list_topics(self, callback: Callable):
        """dunno"""
        super().list_topics(callback)

    def cancel(self):
        """Cancel subscription."""
        if self.type == MiddlewareType.PRODUCER:
            return
        super().cancel(self.topic)
        