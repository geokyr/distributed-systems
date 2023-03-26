import Crypto
import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pss

class Transaction:
    """
    Class for a transaction in the blockchain

    sender: sender's public key
    sender_id: id of the sender
    receiver: receiver's public key
    receiver_id: id of the receiver
    amount: amount of nbc to transfer
    total: total amount that sender sends
    inputs: list of TransactionInput
    id: hash of the transaction
    outputs: list of TransactionOutput
    signature: signature of the transaction
    """

    def __init__(self, sender, sender_id, receiver, receiver_id, amount, total, inputs, id=None, outputs=None, signature=None):
        """Initializes a Transaction"""
        
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
        """Overrides the default method and checks the equality of 2 Transaction
        objects by comparing their hashes"""

        return self.id == transaction.id

    def __str__(self):
        """String representation of a Transaction"""
        
        return str(self.__class__) + ": " + str(self.__dict__)

    def convert_to_list(self):
        """List representation of a Transaction"""
        
        return [self.sender_id, self.receiver_id, self.amount, self.total, self.total - self.amount]

    def hash_transaction(self):
        """Calculates the hash of the Transaction"""

        # The hash is a random integer, at most 256 bits long.
        return Crypto.Random.get_random_bytes(256).decode("ISO-8859-1")

    def calculate_outputs(self):
        """Computes Transaction outputs"""

        self.outputs = [TransactionOutput(self.id, self.receiver, self.amount)]

        if self.total > self.amount:
            # If there is change for the transaction.
            self.outputs.append(TransactionOutput(self.id, self.sender, self.total - self.amount))

    def sign_transaction(self, private_key):
        """Signs the Transaction using a private key"""

        temp = self.id.encode("ISO-8859-1")
        key = RSA.importKey(private_key.encode("ISO-8859-1"))
        hashed = SHA256.new(temp)
        signer = pss.new(key)
        self.signature = signer.sign(hashed).decode("ISO-8859-1")

    def verify_signature(self):
        """Verifies the signature of a Transaction"""

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
    Class for a TransactionInput of a Transaction
    
    output_id: id of the TransactionOutput that is used as TransactionInput
    """

    def __init__(self, output_id):
        """Initiliazes a TransactionInput"""
        
        self.output_id = output_id


class TransactionOutput:
    """
    Class for a TransactionOutput of a Transaction

    transaction_id: id of the transaction
    target: target of the TransactionOutput
    amount: amount of nbc to be credited to the target
    unspent: boolean of whether this output has been used or not
    """

    def __init__(self, transaction_id, target, amount):
        """Initiliazes a TransactionOutput"""

        self.transaction_id = transaction_id
        self.target = target
        self.amount = amount
        self.unspent = True

    def __str__(self):
        """String representation of a Transaction Output object"""

        return str(self.__dict__)
