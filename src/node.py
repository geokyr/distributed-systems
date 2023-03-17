import json
import time
import requests
from Crypto.PublicKey import RSA
from parameters import HEADERS, BOOTSTRAP_IP, BOOTSTRAP_PORT
from wallet import Wallet

class Node:
    def __init__(self):
        self.id = None
        self.wallet = Wallet()
        self.ring = []

        # TODO: chain

    def ip_port_to_address(ip, port):
        return f"http://{ip}:{port}"
        
    def register_node_to_ring(self, id, ip, port, public_key, balance):
        # add this node to the ring, only the bootstrap node can add a node to the ring
        self.ring.append({
            "id": id,
            "ip": ip,
            "port": port,
            "public_key": public_key,
            "balance": balance
        })
        print(f"Node {id} registered to the ring")
        print(self.ring[id])

########################################################################################################


    # def create_new_block():

    # def create_transaction(sender, receiver, signature):
    #     #remember to broadcast it

    # def broadcast_transaction():

    # def validate_transaction():
    #     #use of signature and NBCs balance

    # def add_transaction_to_block():
    #     #if enough transactions  mine

    # def mine_block():

    # def broadcast_block():

    # def valid_proof(.., difficulty=MINING_DIFFICULTY):

    # #concencus functions
    # def valid_chain(self, chain):
    #     #check for the longer chain accroose all nodes

    # def resolve_conflicts(self):
    #     #resolve correct chain
