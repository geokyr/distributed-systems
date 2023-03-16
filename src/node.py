import json
import requests
from Crypto.PublicKey import RSA

class node:
    def __init__(self, host, port, is_bootstrap, number_of_nodes):
        # self.NBC=100;
        ##set
        
        #self.chain
        #self.current_id_count
        #self.NBCs
        #self.wallet

        self.host = host
        self.port = port
        self.is_bootstrap = is_bootstrap
        self.number_of_nodes = number_of_nodes

        # TODO: balance on ring
        self.ring = []
        self.registered_nodes = 0

        self.public_key, self.private_key = self.create_wallet()
        self.ring.append((0, "192.168.2.1", "5000", self.public_key))
        
        # if bootstrap node
        if (is_bootstrap):
            self.ID = 0
            self.NBCs = 100 * self.number_of_nodes
            self.current_transactions = []

            # TODO: unspent_coins add first transaction
            # TODO: genesis block

        else:
            # call bootstrap's api to register node to ring
            address = self.host_port_to_address((host, port))
            public_key = self.public_key
            info = {"address": address, "public_key": public_key}
            json_info = json.dumps(info)

            bootstrap_address = self.host_port_to_address(self.ring[0])
            headers = {'Content-type': 'application/json'}

            requests.post(bootstrap_address + "/register-node", data=json_info, headers=headers)

    def host_port_to_address(host_port):
        id, host, port, public_key = host_port
        return f"http://{host}:{port}"

    def address_to_host_port(address):
        address = address.replace("http://", "")
        host, port = address.split(":")
        return host, port

    def create_wallet():
        # create a wallet for this node, with a public key and a private key
        keys = RSA.generate(2048)
        public_key = keys.publickey().exportKey("PEM").decode()
        private_key = keys.exportKey("PEM").decode()
        return public_key, private_key
        
    def register_node_to_ring(self, address, public_key):
        # add this node to the ring, only the bootstrap node can add a node to the ring
        host, port = self.address_to_host_port(address)
        self.registered_nodes += 1
        self.ring.append((self.registered_nodes, host, port, public_key))
        # TODO: check if all nodes are registered


########################################################################################################


    def create_new_block():

    def create_transaction(sender, receiver, signature):
        #remember to broadcast it

    def broadcast_transaction():

    def validate_transaction():
        #use of signature and NBCs balance

    def add_transaction_to_block():
        #if enough transactions  mine

    def mine_block():

    def broadcast_block():

    def valid_proof(.., difficulty=MINING_DIFFICULTY):

    #concencus functions
    def valid_chain(self, chain):
        #check for the longer chain accroose all nodes

    def resolve_conflicts(self):
        #resolve correct chain
