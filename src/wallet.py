from Crypto.PublicKey import RSA

class Wallet:
    """
    The wallet of a node in the network.

    Attributes:
        private_key (int): the private key of the node.
        public_key (int): the public key of the node (also serves as the node's address).
        transactions (list): a list that contains the transactions of the node.
    """

    def __init__(self):
        """Inits a Wallet"""
        # Generate a private key of key length of 2048 bits.
        key = RSA.generate(2048)

        self.private_key = key.exportKey().decode("ISO-8859-1")
        # Generate the public key from the above private key.
        self.public_key = key.publickey().exportKey().decode("ISO-8859-1")
        self.transactions = []

    def __str__(self):
        """Returns a string representation of a Wallet object."""
        return str(self.__class__) + ": " + str(self.__dict__)

    def wallet_balance(self):
        """Returns the balance of the wallet by iterating through the
            transaction outputs."""

        # The balance of the wallet equals the sum of the UTXOs that
        # have as recipient the current wallet.
        balance = 0
        for transaction in self.transactions:
            for output in transaction.outputs:
                if output.unspent and output.target == self.public_key:
                    balance += output.amount

        return balance
