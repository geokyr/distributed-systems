import pickle
import requests
from parameters import DIFFICULTY
from wallet import Wallet
from block import Blockchain
from transaction import Transaction
from block import Block
import threading
import copy
from collections import deque

class Node:
    def __init__(self):
        self.id = None
        self.wallet = Wallet()
        self.ring = []
        self.chain = Blockchain()
        self.current_block = None
        self.queue = deque()

        self.block_lock = threading.Lock()
        self.queue_lock = threading.Lock()
        self.mining_lock = threading.Lock()
        self.chain_lock = threading.Lock()

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
    
    def create_new_block(self):
        if len(self.chain.blocks) == 0:
            self.current_block = Block(0, 1)
        else:
            self.current_block = Block(None, None)
        return self.current_block

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

        if not self.broadcast_transaction(transaction):
            for transaction in self.wallet.transactions:
                for output in transaction.transaction_outputs:
                    if output.id in inputs:
                        output.unspent = True
            return False

        return True

    def broadcast_transaction(self, transaction):
        def endpoint_post(node, responses, endpoint):
            if node["id"] != self.id:
                address = self.ip_port_to_address(node["ip"], node["port"])
                response = requests.post(address + endpoint,
                                         data=pickle.dumps(transaction))
                responses.append(response.status_code)

        threads = []
        responses = []
        for node in self.ring:
            thread = threading.Thread(target=endpoint_post, args=(
                node, responses, '/validate-transaction'))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for response in responses:
            if response != 200:
                return False
        
        for node in self.ring:
            thread = threading.Thread(target=endpoint_post, args=(
                node, responses, '/receive-transaction'))
            thread.start()

        self.add_transaction_to_block(transaction)
        return True

    def validate_transaction(self, transaction):
        if not transaction.verify_signature():
            return False

        for node in self.ring:
            if node["public_key"] == transaction.sender_address:
                if node["balance"] >= transaction.amount:
                    return True
                return False
        return False

    def add_transaction_to_block(self, transaction):
        if (transaction.sender_address == self.wallet.public_key):
            self.wallet.transactions.append(transaction)
        if (transaction.receiver_address == self.wallet.public_key):
            self.wallet.transactions.append(transaction)
        
        for ring_node in self.ring:
            if ring_node["public_key"] == transaction.sender_address:
                ring_node["balance"] -= transaction.amount
            if ring_node["public_key"] == transaction.receiver_address:
                ring_node["balance"] += transaction.amount

        if self.current_block is None:
            self.current_block = self.create_new_block()

        self.block_lock.acquire()
        if self.current_block.check_block_capacity(transaction):

            self.queue.append(copy.deepcopy(self.current_block))
            self.current_block = self.create_new_block()
            self.block_lock.release()

            with self.queue_lock:
                block_to_mine = self.queue.popleft()
                mined_block = self.mine_block(block_to_mine)
                self.broadcast_block(mined_block)
        else:
            self.block_lock.release()

    def mine_block(self, block):

        block.index = self.chain.blocks[-1].index + 1
        block.previous_hash = self.chain.blocks[-1].current_hash

        while not block.create_hash().startswith('0' * DIFFICULTY):
            with self.mining_lock:
                block.nonce += 1
        block.current_hash = block.create_hash()

        return block

    def broadcast_block(self, block):
        accepted = False

        def send_block(node, responses):
            if node['id'] != self.id:
                address = self.ip_port_to_address(node["ip"], node["port"])
                response = requests.post(address + '/receive-block',
                                         data=pickle.dumps(block))
                responses.append(response.status_code)

        threads = []
        responses = []
        for node in self.ring:
            thread = threading.Thread(target=send_block, args=(
                node, responses))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for response in responses:
            if response == 200:
                accepted = True

        if accepted:
            with self.chain_lock:
                if self.validate_block(block):
                    self.chain.blocks.append(block)

    def validate_previous_hash(self, block):
        return block.previous_hash == self.chain.blocks[-1].current_hash

    def validate_block(self, block):
        return self.validate_previous_hash(block) and block.current_hash == block.create_hash()

    def resolve_conflicts(self, block):
        def receive_chain(node, chains):
            if node["id"] != self.id:
                address = self.ip_port_to_address(node["ip"], node["port"])
                response = requests.get(address + "/send-chain")
                chain = pickle.loads(response._content)
                chains.append(chain)

        threads = []
        chains = []
        for node in self.ring:
            thread = threading.Thread(target=receive_chain, args=(
                node, chains))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        longest_chain = self.chain
        for chain in chains:
            if self.validate_chain(chain) and len(chain.blocks) > len(longest_chain.blocks):
                longest_chain = chain

        with self.chain_lock:
                self.chain = longest_chain
        
        return self.validate_block(block)

    def validate_chain(self, chain):
        blocks = chain.blocks

        if blocks[0].previous_hash != 1 or blocks[0].current_hash != blocks[0].create_hash():
            return False

        for i in range(1, len(blocks)):
            if not blocks[i].current_hash == blocks[i].create_hash() or not blocks[i].previous_hash == blocks[i - 1].current_hash:
                return False
        return True
