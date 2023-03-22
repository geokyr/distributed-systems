import json
import copy
import pickle
import requests

from flask_cors import CORS
from flask import Flask, jsonify, request
from argparse import ArgumentParser

from parameters import HEADERS, BOOTSTRAP_IP, BOOTSTRAP_PORT, NUMBER_OF_NODES
from node import Node

app = Flask(__name__)
CORS(app)

node = Node()

if __name__ == '__main__':
    parser = ArgumentParser(description='Start a node')
    parser.add_argument('ip', type=str, help='ip address')
    parser.add_argument('port', type=str, help='port to listen on')
    parser.add_argument('-b', '--bootstrap', action='store_true', help='bootstrap node')

    args = parser.parse_args()
    ip = args.ip
    port = args.port
    b = args.bootstrap

    if(b):
        node.initialize_bootstrap_node(BOOTSTRAP_IP, BOOTSTRAP_PORT, NUMBER_OF_NODES)
    else:
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

    print(f"Node with ID {id} registered to the ring")

    data = {}
    data["id"] = id
    data["utxos"] = node.wallet.utxos
    data["utxos_copy"] = node.wallet.utxos_copy

    blocks = []
    for block in node.chain.blocks:
        temp = copy.deepcopy(block.__dict__)
        temp["transactions"] = block.transactions_to_serializable()
        blocks.append(temp)

    data["chain"] = blocks
    message = json.dumps(data)

    if len(node.ring) == NUMBER_OF_NODES:
        node.wait_for_all_nodes_to_register.set()
    
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
    print(f"Sent 100 NBCs to node {receiver_id}")

    return f"Sent 100 NBCs to node {receiver_id}", 200

# node receives the ring from bootstrap node
@app.route('/receive-ring', methods=['POST'])
def receive_ring():
    data = json.loads(request.data)
    ring = {}
    for node_id in data:
        temp = int(node_id)
        ring[temp] = copy.deepcopy(data[node_id])
    node.ring = ring
    return "Ring received from bootstrap node", 200






# # node receives the chain from bootstrap node
# @app.route('/receive-chain', methods=['POST'])
# def receive_chain():
#     node.chain = pickle.loads(request.get_data())

#     print("Chain received from bootstrap node")
#     return jsonify({"message": "Chain received from bootstrap node"})

# # node sends its chain
# @app.route('/send-chain', methods=['GET'])
# def send_chain():
#     return pickle.dumps(node.chain)

# # node validates a transaction
# @app.route('/validate-transaction', methods=['POST'])
# def validate_transaction():
#     transaction = pickle.loads(request.get_data())
    
#     if node.validate_transaction(transaction):
#         return jsonify({"message": "Transaction is valid"}), 200
#     else:
#         return jsonify({'message': "Cannot verify signature of transaction"}), 400

# # node validates a block
# @app.route('/validate-block', methods=['POST'])
# def validate_block():
#     block = pickle.loads(request.get_data())
    
#     node.chain_lock.acquire()
#     if node.validate_block(block):
#         print("Block is valid")
#         node.chain.blocks.append(block)
#         node.chain_lock.release()
#     else:
#         if node.validate_previous_hash(block):
#             print("Block previous hash is valid")
#             node.chain_lock.release()
#             return jsonify({"message": "Cannot verify signature of block"}), 400
#         else:
#             if node.resolve_conflicts(block):
#                 print("There was a conflict")
#                 node.chain.blocks.append(block)
#                 node.chain_lock.release()
#             else:
#                 print("Failed to resolve conflict")
#                 node.chain_lock.release()
#                 return jsonify({"mesage": "Cannot accept block"}), 400
#     print("Finally accepted block")
#     return jsonify({"message": "Received block"}), 200

if __name__ == '__main__':
    app.run(host=ip, port=port)
