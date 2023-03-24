import json
import time
from Crypto.Hash import SHA256

class Block:
    """
    Class for a Block of the blockchain

    index: index of the Block
    timestamp: timestamp of the Block's creation
    transactions: list of the Block's transactions
    nonce: proof-of-work
    previous_hash: hash of the previous Block
    hash: hash of the Block
    """

    def __init__(self, index, previous_hash):
        """Initializes a Block"""

        self.index = index
        self.timestamp = time.time()
        self.transactions = []
        self.nonce = None
        self.previous_hash = previous_hash
        self.hash = None

    def __str__(self):
        """String representation of a Block"""

        return str(self.__class__) + ": " + str(self.__dict__)

    def __eq__(self, block):
        """Overrides the default method and checks the equality of 2 Block
        objects by comparing their hashes"""

        return self.hash == block.hash

    def add_transaction_and_check(self, transaction, capacity):
        """Adds a new transaction in the Block"""

        self.transactions.append(transaction)
        if len(self.transactions) == capacity:
            return True

        return False

    def hash_block(self):
        """Calculates the hash of the Block"""

        # We should compute current hash without using the
        # field self.hash.
        block_list = [self.timestamp, [transaction.id for transaction in self.transactions], self.nonce, self.previous_hash]

        block_dump = json.dumps(block_list.__str__())
        return SHA256.new(block_dump.encode("ISO-8859-1")).hexdigest()

class Blockchain:
    """Class for a blockchain

    blocks: list of validated blocks in the chain"""

    def __init__(self):
        """Initializes a Blockchain"""
        
        self.blocks = []

    def __str__(self):
        """String representation of a Blockchain"""

        return str(self.__class__) + ": " + str(self.__dict__)

    def add_block(self, block):
        """Adds a new block in the chain"""

        self.blocks.append(block)
