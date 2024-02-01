"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket
import traceback


class Message:
    """Message Type."""
    def __init__(self, msg_type: str):
        """Initialize message."""
        self._type = msg_type
        # self._timestamp = timestamp
        # self._data = user

    def __repr__(self) -> str:
        """Return a string representation of the message."""
        # return self.__str__()
        return json.dumps({"command": self._type})
    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self, msg_type: str, channel: str):
        super().__init__(msg_type)
        self._channel = channel


    def __repr__(self) -> str:
        return json.dumps({"command": self._type, "channel": self._channel})


class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, msg_type: str, user: str):
        super().__init__(msg_type)
        self._username = user


    def __repr__(self) -> str:
        return json.dumps({"command": self._type, "user": self._username})
    
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, msg_type: str, msg: str, channel: str, timestamp: datetime):
        super().__init__(msg_type)
        self._message = msg

        if channel:
            self._channel = channel
        else:
            self._channel = None
 
        if timestamp:
            self._timestamp = int(timestamp)
        else:
            self._timestamp = int(datetime.now().timestamp())


    def __repr__(self) -> str:
        if self._channel:
            return json.dumps({"command": self._type, "message": self._message.strip(), "channel": self._channel, "ts": self._timestamp})
        else:
            return json.dumps({"command": self._type, "message": self._message.strip(), "ts": self._timestamp})
class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        command = "register"
        return RegisterMessage(command, username)


    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        command = "join"
        return JoinMessage(command, channel)
    
    @classmethod
    def message(cls, message: str, channel: str = "") -> TextMessage:
        """Creates a TextMessage object."""
        command = "message"
        timestamp = datetime.now().timestamp()
        if channel:
            return TextMessage(command, message, channel, timestamp)
        return TextMessage(command, message, None, timestamp)



    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""

        msg_bytes = len(str(msg)).to_bytes(2, "big")
        message = str(msg).encode("utf-8")

        connection.send(msg_bytes + message)



    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        # msg_size = int.from_bytes(connection.recv(2),'big')
        msg_size = connection.recv(2)
        msg_size = int.from_bytes(msg_size, "big")
        # msg = connection.recv(msg_size).decode("utf-8")

        if msg_size:
            try:
                msg = connection.recv(msg_size)
                print("CHEGUEII")
    
                print("não cheguei")
                msg = msg.decode('utf-8')
                print("tipo msg", msg)
                # if msg[-1] != "}":
                #     msg = msg + "}" 
                msg = json.loads(msg)
                
                print("aqui???????")
                msg_type = msg["command"]
                
                if msg_type == "register":
                    return RegisterMessage(msg_type, msg["user"])
                elif msg_type == "join":
                    return JoinMessage(msg_type, msg["channel"])
                elif msg_type == "message":
                    
                    if "channel" in msg.keys():
                        return TextMessage(msg_type, str(msg["message"]), msg["channel"], msg["ts"])
                    else:
                        return TextMessage(msg_type, str(msg["message"]), None, msg["ts"])
                else:
                    # print("AQUI")
                    raise CDProtoBadFormat()
            except json.JSONDecodeError:
                # print("ALI")
                raise CDProtoBadFormat()
        
        



class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
