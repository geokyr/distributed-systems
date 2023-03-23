import json
import copy
import requests

from flask_cors import CORS
from flask import Flask, request
from argparse import ArgumentParser

from parameters import HEADERS, BOOTSTRAP_IP, BOOTSTRAP_PORT, NUMBER_OF_NODES
from node import Node
from transaction import Transaction
from block import Block

app = Flask(__name__)
CORS(app)

node = Node()

if __name__ == '__main__':
    parser = ArgumentParser(description='start a node')
    parser.add_argument('-b', '--bootstrap', action='store_true', help='bootstrap')
    parser.add_argument('ip', nargs='?', help='ip of node')
    parser.add_argument('port', nargs='?', help='port of node')
    args = parser.parse_args()    

    if(args.bootstrap):
        ip, port = BOOTSTRAP_IP, BOOTSTRAP_PORT
        node.initialize_bootstrap_node(BOOTSTRAP_IP, BOOTSTRAP_PORT, NUMBER_OF_NODES)
    else:
        ip, port = args.ip, args.port
        node.request_to_join_ring(ip, port)

# bootstrap node registers another node to the ring
@app.route('/register-node', methods=['POST'])
def register_node():
    ip = request.json["ip"]
    port = request.json["port"]
    public_key = request.json["public_key"]
    id = len(node.ring)

    node.register_node_to_ring(
        id,
        ip,
        port,
        public_key)

    blocks = []
    for block in node.chain.blocks:
        temp = copy.deepcopy(block.__dict__)
        temp["transactions"] = block.transactions_to_serializable()
        blocks.append(temp)

    data = {
        "id": id,
        "utxos": node.wallet.utxos,
        "utxos_copy": node.wallet.utxos_copy,
        "chain": blocks
    }
    
    message = json.dumps(data)

    if len(node.ring) == NUMBER_OF_NODES:
        node.all_nodes_registered()

    print(f"Bootstrap: Node with ID {id} joined the ring and received the chain")
    
    return message, 200

# bootstrap node sends 100 NBCs to node
@app.route('/send-nbcs', methods=['POST'])
def send_nbcs():
    public_key = request.json["public_key"]
    receiver_id = node.get_id_from_public_key(public_key)

    node.create_transaction(
        node.wallet.public_key,
        node.id,
        public_key,
        receiver_id,
        100)
    print(f"Bootstrap: Initial {node.id} -> {receiver_id}: 100 NBCs")
    return f"Initial {node.id} -> {receiver_id}: 100 NBCs", 200

# node receives the ring from bootstrap node
@app.route('/receive-ring', methods=['POST'])
def receive_ring():
    data = json.loads(request.data)

    ring = {}
    for node_id in data:
        ring[int(node_id)] = copy.deepcopy(data[node_id])
    node.ring = ring
    print(f"Ring received from bootstrap node on {node.id}")
    return "OK", 200

# node receives a transaction
@app.route('/receive-transaction', methods=['POST'])
def receive_transaction():
    data = json.loads(request.data)

    transaction = Transaction(**data)

    if transaction in node.received_as_block:
        print("Transcation already received as part of a block")
        return "Transcation already received as part of a block", 200

    message = node.validate_transaction(transaction, node.wallet.utxos)

    if message == "valid":
        mining_started = node.add_transaction_to_valid(transaction)

        node.try_validate_received()

        if mining_started:
            print("Valid transaction, added to block and started mining")
            return "Valid transaction, added to block and started mining", 200
        else:
            print("Valid transaction, added to block")
            return "Valid transaction, added to block", 200

    elif message == "not ready":
        node.add_transaction_to_received(transaction)
        print("Transaction added to received and is waiting to be validated")
        return "Transaction added to received and is waiting to be validated", 200
    else:
        print("Transaction is invalid")
        return "Transaction is invalid", 400

# node receives a block
@app.route('/receive-block', methods=['POST'])
def receive_block():
    data = json.loads(request.data)

    block = Block(int(data["index"]), data["previous_hash"])
    block.timestamp = data["timestamp"]
    block.nonce = data["nonce"]
    block.transactions = [Transaction(**t) for t in data["transactions"]]
    block.hash = data["hash"]

    node.receive_block(block)
    return f"Block {block.index} received", 200

if __name__ == '__main__':
    app.run(host=ip, port=port)
