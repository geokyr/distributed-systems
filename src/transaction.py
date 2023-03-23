import json
import base64
from collections import OrderedDict

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

class Transaction:
    def __init__(self, sender, sender_id, receiver, receiver_id, amount, inputs, outputs=[], id=None, signature=None):
        self.sender = sender
        self.sender_id = sender_id
        self.receiver = receiver
        self.receiver_id = receiver_id
        self.amount = amount
        self.inputs = inputs
        self.id = id
        self.outputs = outputs
        self.signature = signature

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.id == other.id

    def hash_transaction(self):
        temp = OrderedDict([
            ("sender", self.sender),
            ("receiver", self.receiver),
            ("amount", self.amount),
            ("inputs", self.inputs)
        ])
        hashable = json.dumps(temp).encode()
        return SHA256.new(hashable)

    def sign_transaction(self, private_key):
        hash = self.hash_transaction()
        key = RSA.importKey(private_key)
        signer = pkcs1_15.new(key)
        self.id = hash.hexdigest()
        self.signature = base64.b64encode(signer.sign(hash)).decode()
        return self.signature

    def verify_signature(self):
        hash = self.hash_transaction()
        key = RSA.importKey(self.sender.encode())
        verifier = pkcs1_15.new(key)
        try:
            verifier.verify(hash, base64.b64decode(self.signature))
            return True
        except (ValueError, TypeError):
            return False

# keys = RSA.generate(2048)
# public_key = keys.publickey().exportKey().decode()
# private_key = keys.exportKey().decode()

# trans = Transaction(public_key, 1, public_key, 2, 10, [1])
# trans.sign_transaction(private_key)

# trans.outputs.append({"id": 0, "receiver": public_key, "amount": 0})
# trans.outputs.append({"id": 0, "receiver": public_key, "amount": 10})

# print(trans.id)
# print(trans.signature)
# print(trans.verify_signature())
