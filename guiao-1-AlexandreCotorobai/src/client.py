"""CD Chat client program"""
import fcntl
import logging
import os
import socket
import sys
import selectors

from .protocol import CDProto, CDProtoBadFormat, TextMessage

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""

        self.host = "127.0.0.1" #socket.gethostname()  # as both code is running on same pc
        self.port = 5000  # socket server port number
        self.name = name
        self.channel = "default"
        self.sel = selectors.DefaultSelector()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # instantiate

        #message = input(" -> ")  # take input
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        self.sel.register(sys.stdin, selectors.EVENT_READ, self.got_keyboard_data)
        self.sel.register(self.sock, selectors.EVENT_READ, self.read)

    def got_keyboard_data(self, stdin):
        # self.validate(stdin.read())
        message = stdin.read().strip()
        # print("CHEGUEII ")

        if message.lower().strip() == 'exit':
            self.sel.unregister(self.sock)
            self.sock.close()
            exit(0)

        elif message.startswith("/join"):
            if len(message.split(" ")) == 1:
                print("Only command detected, write a channel to join")
            else:
                message = message[len("/join ") : len(message)]
                self.channel = message
                joinMessage = CDProto.join(message)
                # print("join_mensagem", joinMessage)
                CDProto.send_msg(self.sock, joinMessage)

        elif message.startswith('/register'):
            if len(message.split(" ")) == 1:
                print("Only command detected, write a user name")
            else:
                message = message[len("/register ") : len(message)]
                self.name = message

                registerMessage = CDProto.register(message)
                # print("register_mensagem", registerMessage)

                CDProto.send_msg(self.sock, registerMessage)
        else:
            textMessage = CDProto.message(message, self.channel)
            print("text_mensagem", textMessage)
            CDProto.send_msg(self.sock, textMessage)

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.sock.connect((self.host, self.port))  # connect to the server
        #self.sel.modify(self.sock, selectors.EVENT_READ, self.read)
        self.sock.setblocking(False)
        print("Connected to chat server.")


    def read(self, sock):
        data = CDProto.recv_msg(sock)#.decode()  # receive response

        if type(data) is TextMessage:
            print(data._message)


    def loop(self):
        """Loop indefinetely."""

        while True:
            sys.stdout.write('-> ')
            sys.stdout.flush()
            for k, mask in self.sel.select():
                callback = k.data
                callback(k.fileobj)
