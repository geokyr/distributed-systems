import requests
import pickle
import itertools
import time

from copy import deepcopy
from collections import deque
from threading import Lock, Thread

from wallet import Wallet
from block import Block, Blockchain
from transaction import Transaction, TransactionInput

MINING_DIFFICULTY = 5

class Node:
    """
    Class for a node of the ring

    id: id of the node
    chain: blockchain of the node
    wallet: wallet of the node
    ring: information about others (id, ip, port, public_key, balance)

    filter_lock: lock in order to provide mutual exclusion while filtering blocks
    chain_lock: lock in order to provide mutual exclusion while updating the chain
    block_lock: lock in order to provide mutual exclusion while updating blocks
    
    unconfirmed_blocks: queue that contains all the blocks waiting to be mined
    current_block: the block that the node currently fills with transactions
    capacity: max number of transactions in each block
    stop_mining: flag to stop mining when a confirmed block arrives
    """

    def __init__(self):
        """Initializes a node"""
        
        self.id = None
        self.chain = Blockchain()
        self.wallet = Wallet()
        self.ring = []

        self.filter_lock = Lock()
        self.chain_lock = Lock()
        self.block_lock = Lock()

        self.unconfirmed_blocks = deque()
        self.current_block = None
        self.capacity = None
        self.stop_mining = False

    def __str__(self):
        """String representation of a node"""
        
        return str(self.__class__) + ": " + str(self.__dict__)

    def create_new_block(self):
        """Creates a new block"""
        
        if len(self.chain.blocks) == 0:
            # Genesis block
            self.current_block = Block(0, 1)
        else:
            # Filled out later
            self.current_block = Block(None, None)
        return self.current_block

    def register_node_to_ring(self, id, ip, port, public_key, balance):
        """Registers a new node in the ring, called only by the bootstrap node"""

        self.ring.append(
            {
                'id': id,
                'ip': ip,
                'port': port,
                'public_key': public_key,
                'balance': balance
            })

    def create_transaction(self, receiver, receiver_id, amount):
        """Creates a new transaction, after gathering the inputs from the utxos"""

        # Gather the transaction inputs, using utxos of the node
        inputs = []
        inputs_ids = []
        total = 0
        for transaction in self.wallet.transactions:
            for output in transaction.outputs:
                if (output.target == self.wallet.public_key and output.unspent):
                    inputs.append(TransactionInput(transaction.id))
                    inputs_ids.append(transaction.id)
                    output.unspent = False
                    total += output.amount
            if total >= amount:
                # Stop when the total amount is enough
                break

        if total < amount:
            # If there are not enough coins, the utxos are reverted
            for transaction in self.wallet.transactions:
                for output in transaction.outputs:
                    if output.transaction_id in inputs_ids:
                        output.unspent = True
            return {"mining_time": 0, "success": False}

        transaction = Transaction(
            self.wallet.public_key,
            self.id,
            receiver,
            receiver_id,
            amount,
            total,
            inputs
        )

        # Sign transaction
        transaction.sign_transaction(self.wallet.private_key)

        # Broadcast transaction 
        broadcast = self.broadcast_transaction(transaction)
        mining_time = broadcast["mining_time"]
        success = broadcast["success"]

        if not success:
            for transaction in self.wallet.transactions:
                for output in transaction.outputs:
                    if output.transaction_id in inputs_ids:
                        output.unspent = True
            return {"mining_time": mining_time, "success": False}

        return {"mining_time": mining_time, "success": True}

    def add_transaction_to_block(self, transaction):
        """Adds a transaction to a block, check if mining is needed and update
        the wallet and balances of participating nodes"""

        # Add transaction to the wallet of the sender and the receiver
        if (transaction.sender  == self.wallet.public_key):
            self.wallet.transactions.append(transaction)
        if (transaction.receiver == self.wallet.public_key):
            self.wallet.transactions.append(transaction)

        # Update the balance of the sender and the receiver
        for ring_node in self.ring:
            if ring_node['public_key'] == transaction.sender:
                ring_node['balance'] -= transaction.amount
            if ring_node['public_key'] == transaction.receiver:
                ring_node['balance'] += transaction.amount

        # If chain has only the genesis block, create new block
        if self.current_block is None:
            self.current_block = self.create_new_block()

        self.block_lock.acquire()
        if self.current_block.add_transaction_and_check(transaction, self.capacity):
            start_time = time.time()

            # Add the block to the mining queue, create a new one, 
            # mine the first block of the queue and when mining is done
            # broadcast the mined block

            self.unconfirmed_blocks.append(deepcopy(self.current_block))
            self.current_block = self.create_new_block()
            self.block_lock.release()
            while True:
                with self.filter_lock:
                    if (self.unconfirmed_blocks):
                        mined_block = self.unconfirmed_blocks.popleft()
                        mining_result = self.mine_block(mined_block)
                        if (mining_result):
                            break
                        else:
                            self.unconfirmed_blocks.appendleft(mined_block)
                    else:
                        return 0
            mining_time = time.time() - start_time
            self.broadcast_block(mined_block)
            return mining_time
        else:
            self.block_lock.release()
            return 0

    def broadcast_transaction(self, transaction):
        """Broadcasts a transaction to the network, utilizing threads"""

        def thread_func(node, responses, endpoint):
            address = 'http://' + node['ip'] + ':' + node['port']
            response = requests.post(address + endpoint,
                                        data=pickle.dumps(transaction))
            responses.append(response.status_code)

        threads = []
        responses = []
        for node in self.ring:
            if node['id'] != self.id:
                thread = Thread(target=thread_func, args=(
                    node, responses, '/validate_transaction'))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

        for res in responses:
            if res != 200:
                return {"mining_time": 0, "success": False}
        
        for node in self.ring:
            if node['id'] != self.id:
                thread = Thread(target=thread_func, args=(
                    node, responses, '/receive_transaction'))
                thread.start()

        mining_time = self.add_transaction_to_block(transaction)
        return {"mining_time": mining_time, "success": True}

    def validate_transaction(self, transaction):
        """Validates an incoming transaction, by checking the signature,
        the inputs and the outputs"""

        if not transaction.verify_signature():
            return False

        for node in self.ring:
            if node['public_key'] == transaction.sender :
                if node['balance'] >= transaction.amount:
                    return True
        return False

    def mine_block(self, block):
        """Implements the proof-of-work algorithm"""

        block.nonce = 0
        block.index = self.chain.blocks[-1].index + 1
        block.previous_hash = self.chain.blocks[-1].hash

        while (not block.hash_block().startswith('0' * MINING_DIFFICULTY) and not self.stop_mining):
            block.nonce += 1
        block.hash = block.hash_block()

        return not self.stop_mining

    def broadcast_block(self, block):
        """Broadcasts a transaction to the network, utilizing threads"""

        block_accepted = False

        def thread_func(node, responses):
            address = 'http://' + node['ip'] + ':' + node['port']
            response = requests.post(address + '/receive_block',
                                        data=pickle.dumps(block))
            responses.append(response.status_code)

        threads = []
        responses = []
        for node in self.ring:
            if node['id'] != self.id:
                thread = Thread(target=thread_func, args=(node, responses))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

        for response in responses:
            if response == 200:
                block_accepted = True

        if block_accepted:
            with self.chain_lock:
                if self.validate_block(block):
                    self.chain.blocks.append(block)

    def validate_previous_hash(self, block):
        """Validates the previous hash of an incoming block"""

        return block.previous_hash == self.chain.blocks[-1].hash

    def validate_block(self, block):
        """Validates a block, by validating its hash and its previous hash"""

        return self.validate_previous_hash(block) and (block.hash == block.hash_block())

    def filter_blocks(self, mined_block):
        """Filters the queue of the unconfirmed blocks, by removing the
        transactions that are included in a mined block"""
        
        with self.block_lock:
            total_transactions = list(itertools.chain.from_iterable([
                    unc_block.transactions
                    for unc_block
                    in self.unconfirmed_blocks]))

            if (self.current_block):
                total_transactions.extend(self.current_block.transactions)

            self.current_block.transactions = []

            filtered_transactions = [transaction for transaction in total_transactions if (transaction not in mined_block.transactions)]

            if not self.unconfirmed_blocks:
                self.current_block.transactions = deepcopy(filtered_transactions)
                return

            i = 0
            while ((i + 1) * self.capacity <= len(filtered_transactions)):
                self.unconfirmed_blocks[i].transactions = deepcopy(filtered_transactions[i * self.capacity:(i + 1) * self.capacity])
                i += 1

            if i * self.capacity < len(filtered_transactions):
                self.current_block.transactions = deepcopy(filtered_transactions[i * self.capacity:])

            for i in range(len(self.unconfirmed_blocks) - i):
                self.unconfirmed_blocks.pop()

        return

    def share_ring(self, ring_node):
        """Shares your ring to a specified node"""

        address = 'http://' + ring_node['ip'] + ':' + ring_node['port']
        requests.post(address + '/receive_ring', data=pickle.dumps(self.ring))

    def validate_chain(self, blocks):
        """Validates all the blocks of a chain"""

        if (blocks[0].previous_hash != 1 or blocks[0].hash != blocks[0].hash_block()):
            return False

        for i in range(1, len(blocks)):
            if not (blocks[i].hash == blocks[i].hash_block()) or not (blocks[i].previous_hash == blocks[i - 1].hash):
                return False
        return True

    def share_chain(self, ring_node):
        """Shares your blockchain to a specified node"""

        address = 'http://' + ring_node['ip'] + ':' + ring_node['port']
        requests.post(address + '/receive_chain', data=pickle.dumps(self.chain))

    def resolve_conflicts(self, new_block):
        """Resolves conflicts of multiple blockchains, by keeping the longest chain
        when a new block that can't be validated is received"""

        def thread_func(node, chains):
            address = 'http://' + node['ip'] + ':' + node['port']
            response = requests.get(address + "/send_chain")
            new_blockchain = pickle.loads(response._content)
            chains.append(new_blockchain)

        threads = []
        chains = []
        for node in self.ring:
            if node['id'] != self.id:
                thread = Thread(target=thread_func, args=(node, chains))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

        selected_chain = self.chain
        for chain in chains:
            if (self.validate_chain(chain.blocks) and (len(chain.blocks) > len(selected_chain.blocks))):
                selected_chain = chain

        if selected_chain != self.chain:
            self.stop_mining = True
            with self.filter_lock:
                i = len(selected_chain.blocks) - 1
                while (i > 0 and ((selected_chain.blocks[i].hash != self.chain.blocks[-1].hash))):
                    i -= 1

                for block in reversed(self.chain.blocks[i + 1:]):
                    self.unconfirmed_blocks.appendleft(block)

                for block in selected_chain.blocks[i + 1:]:
                    self.filter_blocks(block)

                self.chain = selected_chain
                self.stop_mining = False
        return self.validate_block(new_block)
