from Crypto.PublicKey import RSA

class Wallet:

    def __init__(self, utxos={}):
        keys = RSA.generate(2048)
        self.public_key = keys.publickey().exportKey().decode()
        self.private_key = keys.exportKey().decode()
        self.utxos = utxos
        self.utxos_copy = {}

    def wallet_balance(self):
        balance = 0
        for utxo in self.utxos[self.public_key]:
            balance += utxo["amount"]
        return balance

# wallet = Wallet()

# from transaction import Transaction
# trans = Transaction(wallet.public_key, 1, wallet.public_key, 2, 10, [1])
# wallet.utxos[wallet.public_key] = []
# wallet.utxos[wallet.public_key].append({"id": 1, "receiver": wallet.public_key, "amount": 10})

# print(wallet.wallet_balance())
