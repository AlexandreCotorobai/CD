"""CD Chat server program."""
import logging
import select
import socket
import selectors

from .protocol import CDProto, JoinMessage, TextMessage, RegisterMessage

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    """Chat Server process."""

    def __init__(self):
        try:
            self.sel = selectors.DefaultSelector()

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(("127.0.0.1", 5000))
            self.sock.listen(50)
            # self.sock.setblocking(False)

            self.sel.register(self.sock, selectors.EVENT_READ, self.accept)

            self.channel_list = dict()

        except socket.error as msg:
            print("Error.." + str(msg))

        


    def accept(self, sock, mask):

        self.conn, self.addr = sock.accept()  # Should be ready
        
        self.conn.setblocking(False)

        #msg = CDProto.recv_msg(conn) # To be checked
        #data = conn.recv(1000)

        if "default" in self.channel_list:
            self.channel_list["default"].append(self.conn)
        else:
            self.channel_list["default"] = [self.conn]

        print('accepted', self.conn, 'from', self.addr)

        self.sel.register(self.conn, selectors.EVENT_READ, self.read)


    def read(self, conn, addr):
    
        try:
            data = CDProto.recv_msg(conn)
    
            if data:
                if type(data) is JoinMessage:
                    channel_to_join_registed = False
                    for registedChannel in self.channel_list.keys():
                        if conn in self.channel_list[registedChannel]:
                            self.channel_list[registedChannel].remove(conn)
                        
                        if data._channel == registedChannel:
                            channel_to_join_registed = True

                    if channel_to_join_registed:
                        self.channel_list[data._channel].append(conn)
                    else:
                        self.channel_list[data._channel] = [conn]

                elif type(data) is TextMessage:

                    for c in self.channel_list[data._channel]:
                        
                        CDProto.send_msg(c, data)

                print('echoing', repr(data), 'to', conn)

            else:
                print('closing', conn)
                self.sel.unregister(conn)
                conn.close()
                # self.channel_list["default"].remove(conn)
                for key in self.channel_list.keys():
                    if conn in self.channel_list[key]:
                        self.channel_list[key].remove(conn)    
                
        except (socket.timeout,socket.error):
            self.sel.unregister(conn)
            conn.close()
            # self.channel_list["default"].remove(conn)
            for key in self.channel_list.keys():
                if conn in self.channel_list[key]:
                    self.channel_list[key].remove(conn)      
                

    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
