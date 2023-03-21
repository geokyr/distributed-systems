import time
import json
from Crypto.Hash import SHA256
from parameters import CAPACITY
 
class Blockchain:
    def __init__(self):
        self.blocks = []

    def __str__(self):
        return str(self.__dict__)

    def add_block(self, block):
        self.blocks.append(block)

class Block:
    def __init__(self, index, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = []
        self.nonce = 0
        self.current_hash = None
        self.previous_hash = previous_hash

    def __str__(self):
        return str(self.__dict__)
        
    def create_hash(self):
        temp = self.__dict__.copy()
        temp.pop("current_hash", None)
        temp.pop("transactions", None)

        hashable = json.dumps(temp, sort_keys=True).encode()
        return SHA256.new(hashable).hexdigest()

    def block_full_capacity(self):
        if len(self.transactions) == CAPACITY:
            return True

        return False

# block = Block(0, -1)

# from Crypto.PublicKey import RSA
# keys = RSA.generate(2048)
# public_key = keys.publickey().exportKey().decode()
# private_key = keys.exportKey().decode()

# from transaction import Transaction
# trans = Transaction(public_key, "receiver", 10, 10, [0])
# trans.sign_transaction(private_key)

# block.transactions.append(trans)
# block.transactions.append(trans)

# print(block)
# print([str(transaction) for transaction in block.transactions])

# chain = Blockchain()
# chain.add_block(block)
# print(chain)
# print([str(block) for block in chain.blocks])

# print([str(transaction) for transaction in chain.blocks[0].transactions])
