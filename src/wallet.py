from Crypto.PublicKey import RSA

class Wallet:

    def __init__(self):
        keys = RSA.generate(2048)
        self.public_key = keys.publickey().exportKey().decode()
        self.private_key = keys.exportKey().decode()
        self.transactions = []

    def get_balance(self):
        balance = 0
        for transaction in self.transactions:
            for output in transaction.transaction_outputs:
                if output.unspent and output.receiver == self.public_key:
                    balance += output.amount
        return balance

# wallet = Wallet()
# print(wallet.public_key)
# print(wallet.private_key)
# print(wallet.get_balance())