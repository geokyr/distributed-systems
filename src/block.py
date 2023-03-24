import json
import time
from Crypto.Hash import SHA256

class Block:
    """
    A block in the blockchain.

    Attributes:
        index (int): the sequence number of the block.
        timestamp (float): timestamp of the creation of the block.
        transactions (list): list of all the transactions in the block.
        nonce (int): the solution of proof-of-work.
        previous_hash (hash object): hash of the previous block in the blockchain.
        hash (hash object): hash of the block.
    """

    def __init__(self, index, previous_hash):
        """Inits a Block"""
        self.index = index
        self.timestamp = time.time()
        self.transactions = []
        self.nonce = None
        self.previous_hash = previous_hash
        self.hash = None

    def __str__(self):
        """Returns a string representation of a Block object"""
        return str(self.__class__) + ": " + str(self.__dict__)

    def __eq__(self, block):
        """Overrides the default method for comparing Block objects.

        Two blocks are equal if their hash is equal.
        """
        return self.hash == block.hash

    def add_transaction_and_check(self, transaction, capacity):
        """Adds a new transaction in the block."""

        self.transactions.append(transaction)
        if len(self.transactions) == capacity:
            return True

        return False

    def hash_block(self):
        """Computes the current hash of the block."""

        # We should compute current hash without using the
        # field self.hash.
        block_list = [self.timestamp, [transaction.id for transaction in self.transactions], self.nonce, self.previous_hash]

        block_dump = json.dumps(block_list.__str__())
        return SHA256.new(block_dump.encode("ISO-8859-1")).hexdigest()

class Blockchain:
    """
    The blockchain of the noobcash

    Attributes:
        blocks (list): list that contains the validated blocks of the chain.
    """

    def __init__(self):
        """Inits a Blockchain"""
        self.blocks = []

    def __str__(self):
        """Returns a string representation of a Blockchain object"""
        return str(self.__class__) + ": " + str(self.__dict__)

    def add_block(self, block):
        """Adds a new block in the chain."""
        self.blocks.append(block)
