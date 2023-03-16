import time
import json
import hashlib
from parameters import DIFFICULTY
 
class Block:
    def __init__(self, index, transactions, nonce, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.nonce = nonce
        self.current_hash = None
        self.previous_hash = previous_hash

    def block_to_json(self):
        return json.dumps(dict(index=self.index,
            timestamp=self.timestamp,
            transactions=self.transactions,
            nonce=self.nonce,
            current_hash=self.current_hash,
            previous_hash=self.previous_hash), sort_keys=True)
        
    def create_hash(self):
        json = json.loads(self.block_to_json())
        del json['current_hash']
        hashable = json.dumps(json, sort_keys=True).encode()
        return hashlib.sha256(hashable).hexdigest()

    def mine_block(self):
        while self.create_hash()[:DIFFICULTY] != '0' * DIFFICULTY:
            self.nonce += 1
        self.current_hash = self.create_hash()
        return self


######################################################################

    def add_transaction(transaction transaction, blockchain blockchain):
        # add a transaction to the block