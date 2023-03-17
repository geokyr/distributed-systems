import json
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

class Transaction:

    def __init__(self, sender_address, receiver_address, amount):
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.amount = amount
        self.transaction_id = None
        self.transaction_inputs = []
        self.transaction_outputs = []
        self.signature = None

    def create_hash_object(self):
        temp = self.__dict__.copy()
        temp.pop("transaction_id", None)
        temp.pop("signature", None)

        hashable = json.dumps(temp, sort_keys=True).encode()
        return SHA256.new(hashable)

    def sign_transaction(self, private_key):
        self.transaction_id = self.create_hash_object()
        rsa = RSA.importKey(private_key.encode())
        signer = pkcs1_15.new(rsa)
        self.signature = signer.sign(self.transaction_id)
        return

    def verify_signature(self, public_key):
        hash = self.create_hash_object()
        rsa = RSA.importKey(public_key.encode())
        verifier = pkcs1_15.new(rsa)
        try:
            verifier.verify(hash, self.signature)
            return True
        except (ValueError, TypeError):
            return False

# trans = Transaction("sender", "receiver", 10)
# keys = RSA.generate(2048)
# public_key = keys.publickey().exportKey().decode()
# private_key = keys.exportKey().decode()

# print(trans.__dict__)
# trans.sign_transaction(private_key)
# print(trans.transaction_id)
# print(trans.signature)
# print(trans.verify_signature(public_key))
