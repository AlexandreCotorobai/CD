""" Chord DHT node implementation. """
import socket
import threading
import logging
import pickle
from utils import dht_hash, contains

class FingerTable:
    """Finger Table."""

    def __init__(self, node_id, node_addr, m_bits=10):
        """ Initialize Finger Table."""
        self.m_bits = m_bits
        self.node_id = node_id
        self.node_addr = node_addr
        self.table = {}

    def fill(self, node_id, node_addr):
        """ Fill all entries of finger_table with node_id, node_addr."""
        for i in range(self.m_bits):
            self.table[i+1] = (node_id, node_addr)

    def update(self, index, node_id, node_addr):
        """Update index of table with node_id and node_addr."""
        self.table[index] = (node_id, node_addr)

    def find(self, identification):
        """ Get node address of closest preceding node (in finger table) of identification. """
        for i in range(self.m_bits, 0, -1):
            if not contains(self.node_id, self.table[i][0], identification):
                return self.table[i][1]
        return self.table[i][1] ### DUVIDA AQUI, RETORNAR PRIMEIRO OU ULTIMO? 
    

    def refresh(self):
        """ Retrieve finger table entries requiring refresh."""
        """ Return list of tuples: (index, node_id, node_addr)"""
        ref_list = []
        
        """
        this would work but we refresh everything because tests
        
        for i in range(self.m_bits):
            calculatedIndex = (self.node_id + 2 ** i) % 2 ** self.m_bits
            if not contains(self.node_id, successor_id, calculatedIndex):
                ref_list.append((i+1, self.table[i+1][0], self.table[i+1][1]))
        
        """

        for i in range(self.m_bits):
            calculatedIndex = (self.node_id + 2 ** i) % 2 ** self.m_bits
            ref_list.append((i+1, calculatedIndex, self.table[i+1][1]))

        return ref_list

    def getIdxFromId(self, id):
        """ Get index of finger table entry corresponding to id."""
        for i in range(self.m_bits):
            calculatedIndex = (self.node_id + 2 ** i) % 2 ** self.m_bits
            if contains(self.node_id, calculatedIndex, id):
                return i+1
                

    def __repr__(self):
        return str(self.table)


    @property
    def as_list(self):
        """return the finger table as a list of tuples: (identifier, (host, port)).
        NOTE: list index 0 corresponds to finger_table index 1
        """
        return [(self.table[x]) for x in self.table.keys()]

class DHTNode(threading.Thread):
    """ DHT Node Agent. """

    def __init__(self, address, dht_address=None, timeout=3):
        """Constructor
        
        Parameters:
            address: self's address
            dht_address: address of a node in the DHT
            timeout: impacts how often stabilize algorithm is carried out
        """
        threading.Thread.__init__(self)
        self.done = False
        self.identification = dht_hash(address.__str__())
        self.addr = address  # My address
        self.dht_address = dht_address  # Address of the initial Node
        if dht_address is None:
            self.inside_dht = True
            # I'm my own successor
            self.successor_id = self.identification
            self.successor_addr = address
            self.predecessor_id = None
            self.predecessor_addr = None
        else:
            self.inside_dht = False
            self.successor_id = None
            self.successor_addr = None
            self.predecessor_id = None
            self.predecessor_addr = None

        self.finger_table = FingerTable(self.identification, self.addr)    #TODO:DONE create finger_table

        self.keystore = {}  # Where all data is stored
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.logger = logging.getLogger("Node {}".format(self.identification))

    def send(self, address, msg):
        """ Send msg to address. """
        payload = pickle.dumps(msg)
        self.socket.sendto(payload, address)

    def recv(self):
        """ Retrieve msg payload and from address."""
        try:
            payload, addr = self.socket.recvfrom(1024)
        except socket.timeout:
            return None, None

        if len(payload) == 0:
            return None, addr
        return payload, addr

    def node_join(self, args):
        """Process JOIN_REQ message.

        Parameters:
            args (dict): addr and id of the node trying to join
        """

        self.logger.debug("Node join: %s", args)
        addr = args["addr"]
        identification = args["id"]
        if self.identification == self.successor_id:  # I'm the only node in the DHT
            self.successor_id = identification
            self.successor_addr = addr
            #TODO:DONE update finger table
            self.finger_table.fill(identification, addr)
            args = {"successor_id": self.identification, "successor_addr": self.addr}
            self.send(addr, {"method": "JOIN_REP", "args": args})
        elif contains(self.identification, self.successor_id, identification):
            args = {
                "successor_id": self.successor_id,
                "successor_addr": self.successor_addr,
            }
            self.successor_id = identification
            self.successor_addr = addr
            #TODO:DONE update finger table
            self.finger_table.fill(identification, addr)
            self.send(addr, {"method": "JOIN_REP", "args": args})
        else:
            self.logger.debug("Find Successor(%d)", args["id"])
            self.send(self.successor_addr, {"method": "JOIN_REQ", "args": args})
        self.logger.info(self)

    def get_successor(self, args):
        """Process SUCCESSOR message.

        Parameters:
            args (dict): addr and id of the node asking
        """

        self.logger.debug(" Get successor: %s", args)
        #TODO:DONE Implement processing of SUCCESSOR message
        if contains(self.predecessor_id, self.identification, args["id"]):
            self.send(args["from"], {"method": "SUCCESSOR_REP", "args": {
                "req_id": args["id"],
                "successor_id": self.identification,
                "successor_addr": self.addr,
            }})
        elif contains(self.identification, self.successor_id, args["id"]):
            self.send(args["from"], {"method": "SUCCESSOR_REP", "args": {
                "req_id": args["id"],
                "successor_id": self.successor_id,
                "successor_addr": self.successor_addr,
            }})
        else:
            self.logger.debug("Fowarding request to %s to respond with args %s", self.finger_table.find(args["id"]), args)
            self.send(self.finger_table.find(args["id"]), {"method": "SUCCESSOR", "args": args})



                
    def notify(self, args):
        """Process NOTIFY message.
            Updates predecessor pointers.

        Parameters:
            args (dict): id and addr of the predecessor node
        """

        self.logger.debug("Notify: %s", args)
        if self.predecessor_id is None or contains(
            self.predecessor_id, self.identification, args["predecessor_id"]
        ):
            self.predecessor_id = args["predecessor_id"]
            self.predecessor_addr = args["predecessor_addr"]
        self.logger.info(self)

    def stabilize(self, from_id, addr):
        """Process STABILIZE protocol.
            Updates all successor pointers.

        Parameters:
            from_id: id of the predecessor of node with address addr
            addr: address of the node sending stabilize message
        """
        f = open(f'NODE_{self.identification}.txt', "w")
        f.write(f'ID and Address (Timeout time): {self.identification} and {self.addr} (5) \nPredecessor : {self.predecessor_id}\nNode : {self.identification}\nSucessor : {self.successor_id}\nStorage : {self.keystore}\nFinger Table : {self.finger_table}\n')
        f.close()

        self.logger.debug("Stabilize: %s %s", from_id, addr)
        if from_id is not None and contains(
            self.identification, self.successor_id, from_id
        ):
            # Update our successor
            self.successor_id = from_id
            self.successor_addr = addr
            #TODO update finger table
            self.finger_table.update(1, from_id, addr)

        # notify successor of our existence, so it can update its predecessor record
        args = {"predecessor_id": self.identification, "predecessor_addr": self.addr}
        self.send(self.successor_addr, {"method": "NOTIFY", "args": args})

        # TODO refresh finger_table
        ref_list = self.finger_table.refresh()
        for i in ref_list:

            self.send(i[2], {"method": "SUCCESSOR", "args": {
                "id": i[1],
                "from": self.addr
            }})
            # check if a new node appeared that is between the finger table id and the node id



    def put(self, key, value, address):
        """Store value in DHT.

        Parameters:
        key: key of the data
        value: data to be stored
        address: address where to send ack/nack
        """
        key_hash = dht_hash(key)
        self.logger.debug("Put: %s %s", key, key_hash)

        #TODO Replace next code:
        if contains(self.predecessor_id, self.identification, key_hash):
            if key in self.keystore:
                self.send(address, {"method": "NACK"})
            else:
                self.keystore[key] = value
                self.send(address, {"method": "ACK"})
        else:
            new_addr = self.finger_table.find(key_hash)
            self.send(new_addr, {"method": "PUT", "args": {
            "key": key,
            "value": value,
            "from": address 
        }})

    def get(self, key, address):
        """Retrieve value from DHT.

        Parameters:
        key: key of the data
        address: address where to send ack/nack
        """
        key_hash = dht_hash(key)
        self.logger.debug("Get: %s %s", key, key_hash)

        #TODO Replace next code:
        if contains(self.predecessor_id, self.identification, key_hash):
            if key not in self.keystore:
                self.send(address, {"method": "NACK"})
            else:
                self.send(address, {"method": "ACK", "args": self.keystore[key]})
        else:
            new_addr = self.finger_table.find(key_hash)
            self.send(new_addr, {"method": "GET", "args": {
            "key": key,
            "from": address
        }})


    def run(self):
        self.socket.bind(self.addr)

        # Loop untiln joining the DHT
        while not self.inside_dht:
            join_msg = {
                "method": "JOIN_REQ",
                "args": {"addr": self.addr, "id": self.identification},
            }
            self.send(self.dht_address, join_msg)
            payload, addr = self.recv()
            if payload is not None:
                output = pickle.loads(payload)
                self.logger.debug("O: %s", output)
                if output["method"] == "JOIN_REP":
                    args = output["args"]
                    self.successor_id = args["successor_id"]
                    self.successor_addr = args["successor_addr"]
                    #TODO:DONE fill finger table
                    self.finger_table.fill(self.successor_id, self.successor_addr)
                    self.inside_dht = True
                    self.logger.info(self)

        while not self.done:
            payload, addr = self.recv()
            if payload is not None:
                output = pickle.loads(payload)
                self.logger.info("O: %s", output)
                if output["method"] == "JOIN_REQ":
                    self.node_join(output["args"])
                elif output["method"] == "NOTIFY":
                    self.notify(output["args"])
                elif output["method"] == "PUT":
                    self.put(
                        output["args"]["key"],
                        output["args"]["value"],
                        output["args"].get("from", addr),
                    )
                elif output["method"] == "GET":
                    self.get(output["args"]["key"], output["args"].get("from", addr))
                elif output["method"] == "PREDECESSOR":
                    # Reply with predecessor id
                    self.send(
                        addr, {"method": "STABILIZE", "args": self.predecessor_id}
                    )
                elif output["method"] == "SUCCESSOR":
                    # Reply with successor of id
                    self.get_successor(output["args"])
                elif output["method"] == "STABILIZE":
                    # Initiate stabilize protocol
                    self.stabilize(output["args"], addr)
                elif output["method"] == "SUCCESSOR_REP":
                    #TODO Implement processing of SUCCESSOR_REP
                    self.logger.debug("SUCCESSOR_REP: %s", output["args"])
                    idx = self.finger_table.getIdxFromId(output["args"]["req_id"])
                    self.logger.debug("Finger table idx: %s", idx)
                    self.logger.debug("Finger table: %s", self.finger_table)
                    self.finger_table.update(idx, output["args"]["successor_id"], output["args"]["successor_addr"])
                    self.logger.debug("Finger table: %s", self.finger_table)

            else:  # timeout occurred, lets run the stabilize algorithm
                # Ask successor for predecessor, to start the stabilize process
                self.logger.debug("Stabilize: %s %s", self.successor_id, self.successor_addr)
                self.send(self.successor_addr, {"method": "PREDECESSOR"})
                


    def __str__(self):
        return "Node ID: {}; DHT: {}; Successor: {}; Predecessor: {}; FingerTable: {}".format(
            self.identification,
            self.inside_dht,
            self.successor_id,
            self.predecessor_id,
            self.finger_table,
        )

    def __repr__(self):
        return self.__str__()
