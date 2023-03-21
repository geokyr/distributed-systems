from Crypto.PublicKey import RSA

class Wallet:

    def __init__(self):
        keys = RSA.generate(2048)
        self.public_key = keys.publickey().exportKey().decode()
        self.private_key = keys.exportKey().decode()
        self.transactions = []

    def __str__(self):
        return str(self.__dict__)

    def wallet_balance(self):
        balance = 0
        for transaction in self.transactions:
            for output in transaction.transaction_outputs:
                if output.unspent and output.receiver == self.public_key:
                    balance += output.amount
        return balance

# wallet = Wallet()

# from transaction import Transaction
# trans = Transaction(wallet.public_key, "receiver", 10, 50, [0])
# wallet.transactions.append(trans)

# print(wallet.wallet_balance())
# print(wallet)
# print([str(transaction) for transaction in wallet.transactions])
