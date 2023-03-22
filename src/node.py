import copy
import json
import requests
import threading

from parameters import DIFFICULTY, BOOTSTRAP_IP, BOOTSTRAP_PORT, HEADERS
from wallet import Wallet
from blockchain import Blockchain
from transaction import Transaction
from block import Block
from thread import Thread

lock = threading.Lock()

class Node:
    def __init__(self):
        self.id = -1
        self.ring = {}
        self.wallet = Wallet()
        self.chain = Blockchain()
        self.pool = Thread()

        self.received = []
        self.received_as_block = []
        self.valid = []
        self.old = []

    # Helpers
    def ip_port_to_address(self, ip, port):
        return f"http://{ip}:{port}"

    def get_id_from_public_key(self, public_key):
        for id, node in self.ring.items():
            if node["public_key"] == public_key:
                return id

    # Broadcast
    def broadcast(self, message, endpoint):
        data = json.dumps(message)

        for node_id in self.ring:
            if (node_id != self.id):
                address = self.ip_port_to_address(self.ring[node_id]["ip"], self.ring[node_id]["port"])

                requests.post(address + endpoint, data=data, headers=HEADERS)

    # Nodes
    def initialize_bootstrap_node(self, ip, port, number_of_nodes):
        print(f"Initializing the ring with {number_of_nodes} nodes")
        first_transaction = self.create_first_transaction(number_of_nodes)

        self.chain.create_blockchain(first_transaction)

        self.id = 0
        self.register_node_to_ring(
            self.id,
            ip,
            port,
            self.wallet.public_key)
        print("Initialized bootstrap node")

        self.wait_for_all_nodes_to_register = threading.Event()
        thread = threading.Thread(target=self.all_nodes_registered)
        thread.start()

        print("Bootstrap node registered to the ring and waiting for others")

    def request_to_join_ring(self, ip, port):
        bootstrap_address = self.ip_port_to_address(BOOTSTRAP_IP, BOOTSTRAP_PORT)
        data = json.dumps({
            "ip": ip,
            "port": port,
            "public_key": self.wallet.public_key,
        })

        response = requests.post(
            bootstrap_address + "/register-node",
            data=data,
            headers=HEADERS)

        print(f"Node {ip}:{port} requested to join the ring")

        data = response.json()

        self.id = int(data["id"])
        self.wallet.utxos = data["utxos"]
        self.wallet.utxos_copy = data["utxos_copy"]
        self.add_blocks_to_chain(self.chain.blocks, data["chain"])

        print(f"Node {ip}:{port} joined the ring")

        data = json.dumps({
            "public_key": self.wallet.public_key,
        })

        response = requests.post(
            bootstrap_address + "/send-nbcs",
            data=data,
            headers=HEADERS)

        print(f"Node {ip}:{port} received 100 NBCs from bootstrap node")

    def register_node_to_ring(self, id, ip, port, public_key):
        if self.id == 0:
            self.ring[id] = {
                "ip": ip,
                "port": port,
                "public_key": public_key,
            }
            if(self.id != id):
                self.wallet.utxos[public_key] = []
        else:
            print("Node is not the bootstrap node")

    def all_nodes_registered(self):
        self.wait_for_all_nodes_to_register.wait()
        print("All nodes are registered to the ring")

        endpoint = "/receive-ring"
        message = self.ring
        self.broadcast(message, endpoint)

    def create_first_transaction(self, number_of_nodes):
        receiver = self.wallet.public_key
        starting_amount = 100 * number_of_nodes

        data = {}
        data["sender"] = 0
        data["receiver"] = receiver
        data["inputs"] = []
        output_sender = {"id": 0, "to_who": 0, "amount": 0}
        output_receiver = {"id": 0, "to_who": receiver, "amount": starting_amount}
        data["outputs"] = [output_sender, output_receiver]
        data["amount"] = starting_amount
        data["id"] = 0
        data["sender_id"] = -1
        data["receiver_id"] = 0
        data["signature"] = None
        transaction = Transaction(**data)

        init_utxos = {}
        init_utxos[receiver] = [output_receiver]
        self.wallet.utxos = init_utxos
        self.wallet.utxos_copy =copy.deepcopy(init_utxos)
        return transaction

    def add_blocks_to_chain(self, chain, blocks):
        for data in blocks:
            new_block = Block(data.get("index"), data.get("previous_hash"))
            new_block.nonce = data.get("nonce")
            new_block.hash = data.get("hash")
            new_block.timestamp = data.get("timestamp")
            new_block.transactions = []
            for t in data.get("transactions"):
                new_block.transactions.append(Transaction(**t))
            chain.append(new_block)

    def create_transaction(self, sender, sender_id, receiver, receiver_id, amount):
        print(f"Fake transaction created {sender_id} -> {receiver_id} : {amount}")

    # def share_ring(self, ring_node):
    #     address = self.ip_port_to_address(ring_node["ip"], ring_node["port"])
    #     data = pickle.dumps(self.ring)

    #     requests.post(address + "/receive-ring", data=data)

    # def share_chain(self, ring_node):
    #     address = self.ip_port_to_address(ring_node["ip"], ring_node["port"])
    #     data = pickle.dumps(self.chain)

    #     requests.post(address + "/receive-chain", data=data)

    # def create_new_block(self):
    #     if len(self.chain.blocks) == 0:
    #         self.current_block = Block(0, 1)
    #     else:
    #         self.current_block = Block(None, None)

    # def create_transaction(self, receiver_address, required):
    #     sent = 0
    #     inputs = []

    #     for transaction in self.wallet.transactions:
    #         for output in transaction.transaction_outputs:
    #             if output.receiver == self.wallet.public_key and output.unspent:
    #                 inputs.append(output.id)
    #                 output.unspent = False
    #                 sent += output.amount

    #         if sent >= required:
    #             break

    #     if sent < required:
    #         for transaction in self.wallet.transactions:
    #             for output in transaction.transaction_outputs:
    #                 if output.id in inputs:
    #                     output.unspent = True
    #         return False

    #     transaction = Transaction(
    #         self.wallet.public_key,
    #         receiver_address,
    #         required,
    #         sent,
    #         inputs
    #     )
    #     print("Transaction created: ", transaction.__dict__)

    #     transaction.sign_transaction(self.wallet.private_key)
    #     self.add_transaction_to_block(transaction)
    #     self.broadcast_transaction(transaction)
    #     return True

    # def broadcast_transaction(self, transaction):
    #     def send_transaction(node):
    #         address = self.ip_port_to_address(node["ip"], node["port"])
    #         requests.post(address + '/validate-transaction', data=pickle.dumps(transaction))

    #     for node in self.ring:
    #         if node["id"] != self.id:
    #             thread = threading.Thread(target=send_transaction, args=(node,))
    #             thread.start()

    # def validate_transaction(self, transaction):
    #     if not transaction.verify_signature():
    #         return False
    #     print("Transaction verified: ", transaction.__dict__)
    #     for node in self.ring:
    #         if node["public_key"] == transaction.sender_address:
    #             if node["balance"] >= transaction.required:
    #                 self.add_transaction_to_block(transaction)
    #                 return True
    #     return False

    # def add_transaction_to_block(self, transaction):
    #     if (transaction.sender_address == self.wallet.public_key):
    #         self.wallet.transactions.append(transaction)
    #     if (transaction.receiver_address == self.wallet.public_key):
    #         self.wallet.transactions.append(transaction)

    #     for ring_node in self.ring:
    #         if ring_node["public_key"] == transaction.sender_address:
    #             ring_node["balance"] -= transaction.required
    #         if ring_node["public_key"] == transaction.receiver_address:
    #             ring_node["balance"] += transaction.required
    #     print("Balances fixed: ", transaction.__dict__)
    #     if self.current_block == None:
    #         self.create_new_block()

    #     self.block_lock.acquire()
    #     self.current_block.transactions.append(transaction)

    #     if self.current_block.block_full_capacity():
    #         print("Block full, mining...")
    #         self.queue.append(copy.deepcopy(self.current_block))
    #         self.create_new_block()
    #         self.block_lock.release()

    #         if(self.queue):
    #             print("Mining block...")
    #             block_to_mine = self.queue.popleft()
    #             mined_block = self.mine_block(block_to_mine)
    #             with self.chain_lock:
    #                 print("Appending mined block: ", mined_block.__dict__)
    #                 self.chain.blocks.append(mined_block)
    #             self.broadcast_block(mined_block)
    #     else:
    #         self.block_lock.release()

    # def mine_block(self, block):

    #     block.index = self.chain.blocks[-1].index + 1
    #     block.previous_hash = self.chain.blocks[-1].current_hash

    #     while not block.create_hash().startswith('0' * DIFFICULTY):
    #         with self.mining_lock:
    #             block.nonce += 1
    #     block.current_hash = block.create_hash()
    #     print("Block mined: ", block.__dict__)
    #     return block

    # def broadcast_block(self, block):
    #     def send_block(node):
    #         address = self.ip_port_to_address(node["ip"], node["port"])
    #         requests.post(address + '/validate-block',
    #                                     data=pickle.dumps(block))

    #     for node in self.ring:
    #         if node["id"] != self.id:
    #             thread = threading.Thread(target=send_block, args=(node,))
    #             thread.start()

    # def validate_previous_hash(self, block):
    #     return block.previous_hash == self.chain.blocks[-1].current_hash

    # def validate_block(self, block):
    #     print("Validating block: ", block.__dict__)
    #     return self.validate_previous_hash(block) and block.current_hash == block.create_hash()

    # def resolve_conflicts(self, block):
    #     print("Resolving conflicts...")
    #     def receive_chain(node, chains):
    #         address = self.ip_port_to_address(node["ip"], node["port"])
    #         response = requests.get(address + "/send-chain")
    #         chain = pickle.loads(response._content)
    #         chains.append(chain)

    #     threads = []
    #     chains = []
    #     for node in self.ring:
    #         if node["id"] != self.id:
    #             thread = threading.Thread(target=receive_chain, args=(
    #                 node, chains))
    #             threads.append(thread)
    #             thread.start()

    #     for thread in threads:
    #         thread.join()

    #     longest_chain = self.chain
    #     for chain in chains:
    #         if self.validate_chain(chain.blocks) and len(chain.blocks) > len(longest_chain.blocks):
    #             longest_chain = chain

    #     with self.chain_lock:
    #         print("Replacing chain with longest chain: ", longest_chain.__dict__)
    #         self.chain = longest_chain

    #     return self.validate_block(block)

    # def validate_chain(self, blocks):
    #     if blocks[0].previous_hash != 1 or blocks[0].current_hash != blocks[0].create_hash():
    #         return False
    #     print("Validating chain: ", blocks)
    #     for i in range(1, len(blocks)):
    #         if not blocks[i].current_hash == blocks[i].create_hash() or not blocks[i].previous_hash == blocks[i - 1].current_hash:
    #             return False
    #     return True
