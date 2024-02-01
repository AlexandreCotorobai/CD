import json
import pickle
import xml.etree.ElementTree as ET
from src.log import get_logger

class Message:
    def __init__(self, type) -> None:
        self.type = type

class Req_Topics_Message(Message):
    def __init__(self, type) -> None:
        super().__init__(type)

class Rep_Topics_Message(Message):
    def __init__(self, type, args) -> None:
        super().__init__(type)
        self.args = args

class Subscribe_Message(Message):
    def __init__(self, type, args) -> None:
        super().__init__(type)
        self.args = args

class Unsuscribe_Message(Message):
    def __init__(self, type, args) -> None:
        super().__init__(type)
        self.args = args

class Create_Topic_Message(Message):
    def __init__(self, type, args) -> None:
        super().__init__(type)
        self.args = args

class Publish_Message(Message):
    def __init__(self, type, args) -> None:
        super().__init__(type)
        self.args = args

class Notify_Message(Message):
    def __init__(self, type, args) -> None:
        super().__init__(type)
        self.args = args

class Protocol:
    """Protocol"""
    
    @classmethod
    def subscribe(cls, topic, Serializer) -> Subscribe_Message:
        """Subscribe to a topic."""
        return Subscribe_Message("subscribe", {"topic": topic, "serializer": Serializer})
    
    @classmethod
    def unsubscribe(cls, topic) -> Unsuscribe_Message:
        """Unsubscribe from a topic."""
        return Unsuscribe_Message("unsubscribe", {"topic": topic})
    
    @classmethod
    def create_topic(cls, topic) -> Create_Topic_Message:
        """Create a topic."""
        return Create_Topic_Message("create_topic", {"topic": topic})

    @classmethod
    def publish(cls, topic, data) -> Publish_Message:
        """Publish data to a topic."""
        return Publish_Message("publish", {"topic": topic, "data": data})
    
    @classmethod
    def notify(cls, topic, data) -> Notify_Message:
        """Notify data to a topic."""
        return Notify_Message("notify", {"topic": topic, "data": data})
    
    @classmethod
    def req_topics(cls) -> Req_Topics_Message:
        """Request topics."""
        return Req_Topics_Message("req_topics")
    
    @classmethod
    def rep_topics(cls, topics) -> Rep_Topics_Message:
        """Reply topics."""
        return Rep_Topics_Message("rep_topics", {"topics": topics})
    
    @classmethod
    def to_json(cls, message) -> bytes:
        """Converts message to JSON."""
        if message.type == "req_topics":
            msg = {"type": message.type}
        else:
            msg = {"type": message.type, "args": message.args}
        return json.dumps(msg).encode("utf8")
        
    @classmethod
    def from_json(cls, json_str) -> Message:
        """Converts JSON to message."""
        data = json.loads(json_str)
        if data["type"] == "subscribe":
            return Subscribe_Message(data["type"], data["args"])
        elif data["type"] == "unsubscribe":
            return Unsuscribe_Message(data["type"], data["args"])
        elif data["type"] == "create_topic":
            return Create_Topic_Message(data["type"], data["args"])
        elif data["type"] == "publish":
            return Publish_Message(data["type"], data["args"])
        elif data["type"] == "notify":
            return Notify_Message(data["type"], data["args"])
        elif data["type"] == "req_topics":
            return Req_Topics_Message(data["type"])
        elif data["type"] == "rep_topics":
            return Rep_Topics_Message(data["type"], data["args"])
        else:
            raise ValueError("Invalid message type")
    
    @classmethod
    def to_pickle(cls, message) -> bytes:
        """Converts message to pickle."""
        return pickle.dumps(message)
    
    @classmethod
    def from_pickle(cls, pickle_str) -> Message:
        """Converts pickle to message."""
        data = pickle.loads(pickle_str)
        if data.type == "subscribe":
            return Subscribe_Message(data.type, data.args)
        elif data.type == "unsubscribe":
            return Unsuscribe_Message(data.type, data.args)
        elif data.type == "create_topic":
            return Create_Topic_Message(data.type, data.args)
        elif data.type == "publish":
            return Publish_Message(data.type, data.args)
        elif data.type == "notify":
            return Notify_Message(data.type, data.args)
        elif data.type == "req_topics":
            return Req_Topics_Message(data.type)
        elif data.type == "rep_topics":
            return Rep_Topics_Message(data.type, data.args)
        else:
            raise ValueError("Invalid message type")
    
    @classmethod
    def to_xml(cls, message) -> bytes:
        """Converts message to XML."""
        root = ET.Element("message")
        ET.SubElement(root, "type").text = str(message.type)
        args = ET.SubElement(root, "args")
        for key, value in message.args.items():
            ET.SubElement(args, key).text = str(value)
        
        return ET.tostring(root, encoding="utf8", method="xml")
    
    @classmethod
    def from_xml(cls, xml_str) -> Message:
        """Converts XML to message."""
        parser = ET.XMLParser(encoding="utf-8")
        root = ET.fromstring(xml_str, parser=parser)
        if root.find("type").text == "subscribe":
            return Subscribe_Message(root.find("type").text, {child.tag: child.text for child in root.find("args")})
        elif root.find("type").text == "unsubscribe":
            return Unsuscribe_Message(root.find("type").text, {child.tag: child.text for child in root.find("args")})
        elif root.find("type").text == "create_topic":
            return Create_Topic_Message(root.find("type").text, {child.tag: child.text for child in root.find("args")})
        elif root.find("type").text == "publish":
            return Publish_Message(root.find("type").text, {child.tag: child.text for child in root.find("args")})
        elif root.find("type").text == "notify":
            return Notify_Message(root.find("type").text, {child.tag: child.text for child in root.find("args")})
        elif root.find("type").text == "req_topics":
            return Req_Topics_Message(root.find("type").text)
        elif root.find("type").text == "rep_topics":
            return Rep_Topics_Message(root.find("type").text, {child.tag: child.text for child in root.find("args")})
        else:
            raise ValueError("Invalid message type")
        
    @classmethod
    def send(cls, message, socket, format : int = 0) -> None:
        """Sends message to socket."""
        msg = None
        msgsize = None
        serializer = None
        format = int(format)
        if format == 0:
            msg = cls.to_json(message)
            msgsize = len(msg)
            serializer = 0
        elif format == 1:
            msg = cls.to_xml(message)
            msgsize = len(msg)
            serializer = 1
        elif format == 2:
            msg = cls.to_pickle(message)
            msgsize = len(msg)
            serializer = 2
        else:
            raise ValueError("Invalid format")

        # convert message to bytes
        msgsize = msgsize.to_bytes(4, byteorder="big")
        serializer = serializer.to_bytes(1, byteorder="big")
        # send message
        socket.send(msgsize + serializer + msg)

    @classmethod
    def recv(cls, socket) -> Message:
        """Receives message from socket."""
        # receive message size
        msgsize = int.from_bytes(socket.recv(4), byteorder="big")
        # receive serializer
        serializer = int.from_bytes(socket.recv(1), byteorder="big")
        # receive message
        if msgsize == 0:
            return None
        
        msg = socket.recv(msgsize)
        # convert message to string
        if serializer == 0:
            msg = cls.from_json(msg)
            msg.serializer = 0
        elif serializer == 1:
            msg = cls.from_xml(msg)
            msg.serializer = 1
        elif serializer == 2:
            msg = cls.from_pickle(msg)
            msg.serializer = 2
        else:
            raise ValueError("Invalid serializer")
        return msg