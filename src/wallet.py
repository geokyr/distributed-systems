from Crypto.PublicKey import RSA

class Wallet:
    """
    Class for a Wallet of a node

    private_key: private key of the node
    public_key: public key of the node, also its address
    transactions: list that contains the transactions of the wallet
    """

    def __init__(self):
        """Initializes a Wallet"""

        # Generate a private key of key length of 2048 bits
        key = RSA.generate(2048)

        self.private_key = key.exportKey().decode("ISO-8859-1")
        # Generate the public key from the above private key
        self.public_key = key.publickey().exportKey().decode("ISO-8859-1")
        self.transactions = []

    def __str__(self):
        """String representation of a Wallet"""

        return str(self.__class__) + ": " + str(self.__dict__)

    def wallet_balance(self):
        """Calculates balance of the wallet based on the utxos"""

        # Balance of the wallet equals the sum of the UTXOs with
        # the wallet as recipient
        balance = 0
        for transaction in self.transactions:
            for output in transaction.outputs:
                if output.unspent and output.target == self.public_key:
                    balance += output.amount

        return balance
