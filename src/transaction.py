import json
import base64
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

class TransactionOutput:
    id_counter = 0

    def __init__(self, transaction_id, receiver, amount):
        self.id = TransactionOutput.id_counter
        TransactionOutput.id_counter += 1
        self.transaction_id = transaction_id
        self.receiver = receiver
        self.amount = amount
        self.unspent = True

    def __str__(self):
        return str(self.__dict__)

class Transaction:
    def __init__(self, sender_address, receiver_address, required, sent, transaction_inputs):
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.required = required
        self.sent = sent
        self.transaction_inputs = transaction_inputs
        self.transaction_id = None
        self.transaction_outputs = []
        self.signature = None

        self.transaction_id = self.create_hash_object().hexdigest()
        self.transaction_outputs = self.calculate_transaction_outputs()

    def __str__(self):
        return str(self.__dict__)

    def create_hash_object(self):
        temp = self.__dict__.copy()
        temp.pop("transaction_id", None)
        temp.pop("signature", None)
        temp.pop("transaction_outputs", None)

        hashable = json.dumps(temp, sort_keys=True).encode()
        return SHA256.new(hashable)

    def calculate_transaction_outputs(self):
        receiver_output = TransactionOutput(
            self.transaction_id, self.receiver_address, self.required)
        sender_output = TransactionOutput(
            self.transaction_id, self.sender_address, self.sent - self.required)
        return [receiver_output, sender_output]

    def sign_transaction(self, private_key):
        temp = self.create_hash_object()
        rsa = RSA.importKey(private_key.encode())
        signer = pkcs1_15.new(rsa)
        self.signature = base64.b64encode(signer.sign(temp)).decode()
        return

    def verify_signature(self):
        hash = self.create_hash_object()
        rsa = RSA.importKey(self.sender_address.encode())
        verifier = pkcs1_15.new(rsa)
        try:
            verifier.verify(hash, base64.b64decode(self.signature))
            return True
        except (ValueError, TypeError):
            return False

# keys = RSA.generate(2048)
# public_key = keys.publickey().exportKey().decode()
# private_key = keys.exportKey().decode()

# trans = Transaction(public_key, "receiver", 10, 10, [0])
# print(trans)
# print([str(output) for output in trans.transaction_outputs])

# trans.sign_transaction(private_key)
# print(trans.transaction_id)
# print(trans.signature)
# print(trans.verify_signature())
