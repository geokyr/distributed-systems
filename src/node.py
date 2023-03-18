import json
import time
import pickle
import requests
from Crypto.PublicKey import RSA
from parameters import HEADERS, BOOTSTRAP_IP, BOOTSTRAP_PORT
from wallet import Wallet
from block import Blockchain
from transaction import Transaction, TransactionOutput

class Node:
    def __init__(self):
        self.id = None
        self.wallet = Wallet()
        self.ring = []
        self.chain = Blockchain()

    def ip_port_to_address(self, ip, port):
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

    def share_ring(self, ring_node):
        address = self.ip_port_to_address(ring_node["ip"], ring_node["port"])
        data = pickle.dumps(self.ring)
        requests.post(address + "/receive-ring", data=data)

    def share_chain(self, ring_node):
        address = self.ip_port_to_address(ring_node["ip"], ring_node["port"])
        data = pickle.dumps(self.chain)
        requests.post(address + "/receive-chain", data=data)
    
    def create_transaction(self, receiver_address, required):
        sent = 0
        inputs = []

        for transaction in self.wallet.transactions:
            for output in transaction.transaction_outputs:
                if output.receiver == self.wallet.public_key and output.unspent:
                    inputs.append(output.id)
                    output.unspent = False
                    sent += output.amount
            
            if sent >= required:
                break
            
        if sent < required:
            for transaction in self.wallet.transactions:
                for output in transaction.transaction_outputs:
                    if output.id in inputs:
                        output.unspent = True
            return False
        
        transaction = Transaction(
            self.wallet.public_key,
            receiver_address,
            required,
            sent,
            inputs
        )

        transaction.sign_transaction(self.wallet.private_key)

        # TODO: broadcast


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
