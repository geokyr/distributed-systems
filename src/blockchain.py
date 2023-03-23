from block import Block

class Blockchain:
    def __init__(self):
        self.blocks = []

    def create_blockchain(self, first_transaction):
        genesis_block = Block(index=0, previous_hash=1)
        genesis_block.transactions.append(first_transaction)
        genesis_block.hash = genesis_block.hash_block()
        self.add_block(genesis_block)

    def add_block(self, new_block):
        self.blocks.append(new_block)
        print(f"Current blockchain length:\t{str(len(self.blocks))}")
        print(f"The blockchain blocks are:")
        self.print_chain()

    def print_chain(self):
        print("-" * 50)
        for block in self.blocks:
            block.print_block()

# from Crypto.PublicKey import RSA
# from transaction import Transaction

# keys = RSA.generate(2048)
# public_key = keys.publickey().exportKey().decode()
# private_key = keys.exportKey().decode()

# trans = Transaction(public_key, 1, public_key, 2, 10, [1])
# trans.sign_transaction(private_key)

# trans.outputs.append({"id": 0, "receiver": public_key, "amount": 0})
# trans.outputs.append({"id": 0, "receiver": public_key, "amount": 10})

# chain = Blockchain()
# chain.create_blockchain(trans)
# chain.add_block(Block(1, chain.blocks[-1].hash))

# chain.print_chain()
