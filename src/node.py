import copy
import json
import requests
import threading

from parameters import DIFFICULTY, CAPACITY, BOOTSTRAP_IP, BOOTSTRAP_PORT, HEADERS
from wallet import Wallet
from blockchain import Blockchain
from transaction import Transaction
from block import Block

lock = threading.Lock()

class Node:
    def __init__(self):
        self.id = -1
        self.ring = {}
        self.wallet = Wallet()
        self.chain = Blockchain()

        self.received = []
        self.received_as_block = []
        self.valid = []
        self.old = []

    # Helpers
    # -------
    def ip_port_to_address(self, ip, port):
        return f"http://{ip}:{port}"

    def get_id_from_public_key(self, public_key):
        for id, node in self.ring.items():
            if node["public_key"] == public_key:
                return id

    # Broadcast
    # ---------
    def broadcast(self, message, endpoint):
        def broadcast_thread(address, endpoint, data):
            requests.post(address + endpoint, data=data, headers=HEADERS)
        
        data = json.dumps(message)

        for node_id in self.ring:
            if (node_id != self.id):
                address = self.ip_port_to_address(self.ring[node_id]["ip"], self.ring[node_id]["port"])
                thread = threading.Thread(target=broadcast_thread, args=(address, endpoint, data))
                thread.start()
                print(f"Broadcast from {self.id} to {address + endpoint}")

    def post_request(self, url, data, headers):
        return requests.post(url, data=data, headers=headers)

    def broadcast_transaction(self, transaction):
        endpoint = "/receive-transaction"
        message = copy.deepcopy(transaction.__dict__)
        self.broadcast(message, endpoint)
        print(f"Transaction {transaction.sender_id} -> {transaction.receiver_id}: {transaction.amount} broadcasted to all")

    def broadcast_block(self, block):
        endpoint = "/receive-block"
        message = copy.deepcopy(block.__dict__)
        message["transactions"] = block.transactions_to_serializable()
        self.broadcast(message, endpoint)
        print(f"Block {block.index} broadcasted to all")

    # Bootstrap and nodes
    # -------------------
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
        print("Bootstrap node registered to the ring")

        # self.wait_for_all_nodes_to_register = threading.Event()
        # thread = threading.Thread(target=self.all_nodes_registered)
        # thread.start()
        print("Bootstrap node waiting for others to join the ring")

    def create_first_transaction(self, number_of_nodes):
        receiver = self.wallet.public_key
        starting_amount = 100 * number_of_nodes

        output_sender = {"id": 0, "target": 0, "amount": 0}
        output_receiver = {"id": 0, "target": receiver, "amount": starting_amount}

        data = {
            "sender": 0,
            "receiver": receiver,
            "inputs": [],
            "outputs": [output_sender, output_receiver],
            "amount": starting_amount,
            "id": 0,
            "sender_id": -1,
            "receiver_id": 0,
            "signature": None
        }

        transaction = Transaction(**data)
        init_utxos = {}
        init_utxos[receiver] = [output_receiver]
        self.wallet.utxos = init_utxos
        self.wallet.utxos_copy =copy.deepcopy(init_utxos)
        return transaction

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

        print(f"Node with ID {self.id} joined the ring and received chain")

        data = json.dumps({
            "public_key": self.wallet.public_key,
        })

        response = requests.post(
            bootstrap_address + "/send-nbcs",
            data=data,
            headers=HEADERS)

        print(response.text)

    def add_blocks_to_chain(self, chain, blocks):
        for data in blocks:
            new_block = Block(data["index"], data["previous_hash"])
            new_block.nonce = data["nonce"]
            new_block.hash = data["hash"]
            new_block.timestamp = data["timestamp"]
            new_block.transactions = []
            for t in data["transactions"]:
                new_block.transactions.append(Transaction(**t))
            chain.append(new_block)

    def all_nodes_registered(self):
        # self.wait_for_all_nodes_to_register.wait()
        print("All nodes are registered to the ring")

        endpoint = "/receive-ring"
        message = self.ring
        self.broadcast(message, endpoint)
        print("Ring broadcasted to all nodes")

    # Transactions
    # ------------
    def create_transaction(self, sender, sender_id, receiver, receiver_id, amount):
        sum = 0
        inputs = []

        try:
            if(self.wallet.wallet_balance() < amount):
                raise Exception("Error: Not enough coins")

            for utxo in self.wallet.utxos[sender]:
                sum += utxo["amount"]
                inputs.append(utxo["id"])
                if(sum >= amount):
                    break

            new_transaction = copy.deepcopy(Transaction(sender, sender_id, receiver, receiver_id, amount, inputs))
            new_transaction.sign_transaction(self.wallet.private_key)
            new_transaction.outputs.append({"id": new_transaction.id, "target": sender, "amount": sum-amount})
            new_transaction.outputs.append({"id": new_transaction.id, "target": receiver, "amount": amount})

            if(self.validate_transaction(new_transaction, self.wallet.utxos) == "valid"):
                self.add_transaction_to_valid(new_transaction)
                # self.broadcast_transaction(new_transaction)
                print(f"Transaction {sender_id} -> {receiver_id}: {amount} created, validated and broadcasted to all")
                return f"Transaction {sender_id} -> {receiver_id}: {amount} created, validated and broadcasted to all"
            else:
                print("Error while validating transaction after creation")
                return "Error while validating transaction after creation"

        except Exception as e:
            print(f"Error while creating transaction: {e}")
            return "Error while creating transaction"

    def validate_transaction(self, transaction, utxos):
        try:
            if not transaction.verify_signature():
                print("Signature not valid")
                return "Error: Signature not valid"

            sender_utxos = copy.deepcopy(utxos[transaction.sender])
            sum = 0

            for transaction_id in transaction.inputs:
                ready = False
                for utxo in sender_utxos:
                    if(utxo["id"] == transaction_id) and utxo["target"] == transaction.sender:
                        sum += utxo["amount"]
                        sender_utxos.remove(utxo)
                        ready = True
                        break
            
                if not ready:
                    print("not ready")
                    return "not ready"

            outputs = []
            if (sum >= transaction.amount):
                outputs.append({"id": transaction.id, "target": transaction.sender, "amount": sum-transaction.amount})
                outputs.append({"id": transaction.id, "target": transaction.receiver, "amount": transaction.amount})
            else:
                print("what is this check #1")

            if outputs != transaction.outputs:
                raise Exception ("Outputs not valid")

            if(transaction.receiver not in utxos.keys()):
                utxos[transaction.receiver] = []

            if(len(transaction.outputs) == 2):
                sender_utxos.append(transaction.outputs[0])
                utxos[transaction.sender] = sender_utxos
                utxos[transaction.receiver].append(transaction.outputs[1])                
            else:
                print("what is this check #2")
                # utxos[transaction.sender] = sender_utxos
                # utxos[transaction.receiver].append(transaction.outputs[0])
            return "valid"

        except Exception as e:
            print(f"Error while validating transaction: {e}")
            return "Error while validating transaction"

    def add_transaction_to_valid(self, transaction):
        self.old.append(transaction)
        self.valid.append(transaction)

        if len(self.valid) == CAPACITY:
            temp = copy.deepcopy(self.valid)
            self.valid = []
            print("After adding transaction to valid, block created and mining started")
            # future = self.pool.executor.submit(
            #     self.create_block_and_mine,
            #     temp)
            return True
        else:
            return False

    def try_validate_received(self):
        for transaction in self.received:
            if self.validate_transaction(transaction, self.wallet.utxos) == "valid":
                self.received = [t for t in self.received if t != transaction]
                self.add_transaction_to_valid(transaction)
                print("Received transaction is now transfered to valid")

    def add_transaction_to_received(self, transaction):
        self.received.append(transaction)

    def remove_from_old(self, transactions):
        self.old = [t for t in self.old if t not in transactions]

    # Blocks
    # ------

    def create_block_and_mine(self, transactions):
        new_block = self.create_new_block(transactions)
        temp = copy.deepcopy(self.wallet.utxos_copy)

        if not self.block_rerun(new_block, temp):
            return
        self.mine_block(new_block)

        lock.acquire()
        if self.validate_block(new_block):
            print("Mined block is valid, adding to chain")
            self.chain.add_block(new_block)

            self.remove_from_old(transactions)
            self.wallet.utxos_copy = temp

            lock.release()
            # self.broadcast_block(new_block)
        else:
            lock.release()

    def create_new_block(self, transactions):
        if len(self.chain.blocks) == 0:
            index, previous_hash = 0, 1
        else:
            last_block = self.chain.blocks[-1]
            index, previous_hash = last_block.index + 1, last_block.hash
        new_block = Block(index, previous_hash)
        new_block.transactions = transactions
        return new_block

    def block_rerun(self, block, utxos):
        for transaction in block.transactions:
            if self.validate_transaction(transaction, utxos) != "valid":
                print(f"Failed to validate transaction {transaction.sender_id} -> {transaction.receiver_id} : {transaction.amount} in block rerun")
                return False
        return True

    def mine_block(self, block):
        while not block.hash_block().startswith('0' * DIFFICULTY):
            block.nonce += 1
        block.hash = block.hash_block()

        print(f"Block {block.index} mined")

    def validate_block(self, block):
        return block.previous_hash == self.chain.blocks[-1].hash and block.hash == block.hash_block()

    def receive_block(self, block):
        temp = copy.deepcopy(self.wallet.utxos_copy)

        if self.block_rerun(block, temp):
            print(f"Received block's {block.index} transactions have rerun successfully")
            lock.acquire()
            if self.validate_block(block):
                print(f"Received block {block.index} is valid, adding to chain")
                self.chain.add_block(block)
                self.wallet.utxos = temp
                self.wallet.utxos_copy = temp
                lock.release()

                self.received = [t for t in self.received if t not in block.transactions]

                new_received_as_block = [t for t in block.transactions if t not in (self.old + self.received)]
                for transaction in new_received_as_block:
                    self.received_as_block.append(transaction)

                new_valid = [t for t in self.old if t not in block.transactions]
                self.valid = []
                self.remove_from_old(block.transactions)

                for transaction in new_valid:
                    self.add_transaction_to_valid(transaction)

                self.try_validate_received()
            else:
                lock.release()
                print(f"Received block {block.index} is not valid, resolve conflicts needed")
                self.resolve_conflicts()
        else:
            print(f"Received block's {block.index} transactions couldn't rerun, resolve conflicts needed")
            self.resolve_conflicts()

    def resolve_conflicts(self):
        print("Resolving conflicts: ...")