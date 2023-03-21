import pickle
import requests
from parameters import DIFFICULTY, NUMBER_OF_NODES
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

    def all_nodes_registered(self):
        self.wait_for_all_nodes_to_register.wait()
        print("All nodes are registered to the ring")

        for ring_node in self.ring[1:]:
            self.share_ring(ring_node)
            self.share_chain(ring_node)

        for ring_node in self.ring[1:]:
            print(self.create_transaction(ring_node["public_key"], 100))

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
        print("Transaction created: ", transaction.__dict__)

        transaction.sign_transaction(self.wallet.private_key)
        self.add_transaction_to_block(transaction)
        self.broadcast_transaction(transaction)
        return True

    def broadcast_transaction(self, transaction):
        def send_transaction(node):
            address = self.ip_port_to_address(node["ip"], node["port"])
            requests.post(address + '/validate-transaction', data=pickle.dumps(transaction))

        for node in self.ring:
            if node["id"] != self.id:
                thread = threading.Thread(target=send_transaction, args=(node,))
                thread.start()

    def validate_transaction(self, transaction):
        if not transaction.verify_signature():
            return False
        print("Transaction verified: ", transaction.__dict__)
        for node in self.ring:
            if node["public_key"] == transaction.sender_address:
                if node["balance"] >= transaction.required:
                    self.add_transaction_to_block(transaction)
                    return True
        return False

    def add_transaction_to_block(self, transaction):
        if (transaction.sender_address == self.wallet.public_key):
            self.wallet.transactions.append(transaction)
        if (transaction.receiver_address == self.wallet.public_key):
            self.wallet.transactions.append(transaction)
        
        for ring_node in self.ring:
            if ring_node["public_key"] == transaction.sender_address:
                ring_node["balance"] -= transaction.required
            if ring_node["public_key"] == transaction.receiver_address:
                ring_node["balance"] += transaction.required
        print("Balances fixed: ", transaction.__dict__)
        if self.current_block == None:
            self.create_new_block()

        self.block_lock.acquire()
        self.current_block.transactions.append(transaction)

        if self.current_block.block_full_capacity():
            print("Block full, mining...")
            self.queue.append(copy.deepcopy(self.current_block))
            self.create_new_block()
            self.block_lock.release()

            if(self.queue):
                print("Mining block...")
                block_to_mine = self.queue.popleft()
                mined_block = self.mine_block(block_to_mine)
                with self.chain_lock:
                    print("Appending mined block: ", mined_block.__dict__)
                    self.chain.blocks.append(mined_block)
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
        print("Block mined: ", block.__dict__)
        return block

    def broadcast_block(self, block):
        def send_block(node):
            address = self.ip_port_to_address(node["ip"], node["port"])
            requests.post(address + '/validate-block',
                                        data=pickle.dumps(block))

        for node in self.ring:
            if node["id"] != self.id:
                thread = threading.Thread(target=send_block, args=(node,))
                thread.start()

    def validate_previous_hash(self, block):
        return block.previous_hash == self.chain.blocks[-1].current_hash

    def validate_block(self, block):
        print("Validating block: ", block.__dict__)
        return self.validate_previous_hash(block) and block.current_hash == block.create_hash()

    def resolve_conflicts(self, block):
        print("Resolving conflicts...")
        def receive_chain(node, chains):
            address = self.ip_port_to_address(node["ip"], node["port"])
            response = requests.get(address + "/send-chain")
            chain = pickle.loads(response._content)
            chains.append(chain)

        threads = []
        chains = []
        for node in self.ring:
            if node["id"] != self.id:
                thread = threading.Thread(target=receive_chain, args=(
                    node, chains))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

        longest_chain = self.chain
        for chain in chains:
            if self.validate_chain(chain.blocks) and len(chain.blocks) > len(longest_chain.blocks):
                longest_chain = chain

        with self.chain_lock:
            print("Replacing chain with longest chain: ", longest_chain.__dict__)
            self.chain = longest_chain
        
        return self.validate_block(block)

    def validate_chain(self, blocks):
        if blocks[0].previous_hash != 1 or blocks[0].current_hash != blocks[0].create_hash():
            return False
        print("Validating chain: ", blocks)
        for i in range(1, len(blocks)):
            if not blocks[i].current_hash == blocks[i].create_hash() or not blocks[i].previous_hash == blocks[i - 1].current_hash:
                return False
        return True

    # TODO: Implement
    def filter_transactions(self):
        pass
