import time
import json
from collections import OrderedDict
from Crypto.Hash import SHA256

from parameters import CAPACITY

class Block:
    def __init__(self, index=-1, previous_hash=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = time.time()
        self.nonce = 0
        self.transactions = []
        self.hash = None
    
    def transactions_to_serializable(self):
        serializable = []
        for transaction in self.transactions:
            serializable.append(transaction.__dict__)
        return serializable

    def hash_block(self):
        temp = OrderedDict([
            ("index", self.index),
            ("previous_hash", self.previous_hash),
            ("timestamp", self.timestamp),
            ("nonce", self.nonce),
            ("transactions", self.transactions_to_serializable())
        ])
        hashable = json.dumps(temp).encode()
        return SHA256.new(hashable).hexdigest()

    def print_block(self):
        print(f"_____Block #{str(self.index)}_____")
        print(f"Timestamp:\t{str(self.timestamp)}")
        print(f"Nonce:\t\t{str(self.nonce)}")
        print(f"Transactions:\t")
        for t in self.transactions:
            print(f"\t\tSender ID: {str(t.sender_id)}\t\tReceiver ID: {str(t.receiver_id)}\t\tAmount: {str(t.amount)} NBCs")
            print(f"\t\tHash: {str(t.id)}")
        print(f"Current Hash:\t{str(self.hash)}")
        print(f"Previous Hash:\t{str(self.previous_hash)}")

# from Crypto.PublicKey import RSA
# from transaction import Transaction

# keys = RSA.generate(2048)
# public_key = keys.publickey().exportKey().decode()
# private_key = keys.exportKey().decode()

# trans = Transaction(public_key, 1, public_key, 2, 10, [1])
# trans.sign_transaction(private_key)

# trans.outputs.append({"id": 0, "receiver": public_key, "amount": 0})
# trans.outputs.append({"id": 0, "receiver": public_key, "amount": 10})

# block = Block(0, 1)
# block.transactions.append(trans)

# block.hash = block.hash_block()
# block.print_block()
