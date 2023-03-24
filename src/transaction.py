import Crypto
import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pss

class Transaction:
    """
    A noobcash transaction in the blockchain

    Attributes:
        sender (int): the public key of the sender's wallet.
        sender_id (int): the id of the sender node.
        receiver (int): the public key of the receiver's wallet.
        receiver_id (int): the id of the receiver node.
        amount (int): the amount of nbc to transfer.
        inputs (list): list of TransactionInput.
        total (int): the amount of money that the sender send for the transaction.
        id (int): hash of the transaction.
        outputs (list): list of TransactionOutput.
        signature (int): signature that verifies that the owner of the wallet created the transaction.
    """

    def __init__(self, sender, sender_id, receiver, receiver_id, amount, total, inputs, id=None, outputs=None, signature=None):
        """Inits a Transaction"""
        self.sender = sender
        self.sender_id = sender_id
        self.receiver = receiver
        self.receiver_id = receiver_id
        self.amount = amount
        self.total = total
        self.inputs = inputs

        if (id):
            self.id = id
        else:
            self.id = self.hash_transaction()

        if (outputs):
            self.outputs = outputs
        else:
            self.calculate_outputs()

        self.signature = signature

    def __eq__(self, transaction):
        """Overrides the default method for comparing Transaction objects.

        Two transactions are equal if their id is equal.
        """
        return self.id == transaction.id

    def __str__(self):
        """Returns a string representation of a Transaction object"""
        return str(self.__class__) + ": " + str(self.__dict__)

    def convert_to_list(self):
        """Converts a Transaction object into a list."""
        return [self.sender_id, self.receiver_id, self.amount, self.total, self.total - self.amount]

    def hash_transaction(self):
        """Computes the hash of the transaction."""

        # The hash is a random integer, at most 256 bits long.
        return Crypto.Random.get_random_bytes(256).decode("ISO-8859-1")

    def calculate_outputs(self):
        """Compute the outputs of the transaction, if not set.

        The computation includes:
            - an output for the nbcs sent to the receiver.
            - an output for the nbcs sent back to the sender as change.
        """

        self.outputs = [TransactionOutput(self.id, self.receiver, self.amount)]

        if self.total > self.amount:
            # If there is change for the transaction.
            self.outputs.append(TransactionOutput(self.id, self.sender, self.total - self.amount))

    def sign_transaction(self, private_key):
        """Sign the current transaction with the given private key."""

        temp = self.id.encode("ISO-8859-1")
        key = RSA.importKey(private_key.encode("ISO-8859-1"))
        hashed = SHA256.new(temp)
        signer = pss.new(key)
        self.signature = signer.sign(hashed).decode("ISO-8859-1")

    def verify_signature(self):
        """Verifies the signature of a transaction."""

        key = RSA.importKey(self.sender.encode("ISO-8859-1"))
        hashed = SHA256.new(self.id.encode("ISO-8859-1"))
        verifier = pss.new(key)
        try:
            verifier.verify(hashed, self.signature.encode("ISO-8859-1"))
            return True
        except (ValueError, TypeError):
            return False

class TransactionInput:
    """
    The transaction input of a noobcash transaction.

    Attributes:
        output_id (int): id of the transaction that the coins come from.
    """

    def __init__(self, output_id):
        """Inits a TransactionInput."""
        self.output_id = output_id


class TransactionOutput:
    """
    A transaction output of a noobcash transaction.

    Attributes:
        transaction_id (int): id of the transaction.
        target (int): the target of the transaction.
        amount (int): the amount of nbcs to be transfered.
        unspent (boolean): false if this output has been used as input in a transaction.
    """

    def __init__(self, transaction_id, target, amount):
        """Inits a TransactionOutput."""
        self.transaction_id = transaction_id
        self.target = target
        self.amount = amount
        self.unspent = True

    def __str__(self):
        """Returns a string representation of a TransactionOutput object"""
        return str(self.__dict__)
