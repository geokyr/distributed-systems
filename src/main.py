import requests
import pickle
import time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from argparse import ArgumentParser
from parameters import HEADERS, BOOTSTRAP_IP, BOOTSTRAP_PORT, NUMBER_OF_NODES
from node import Node
from block import Block
from transaction import Transaction
import json
import threading

app = Flask(__name__)
CORS(app)

# global variables
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
        node.id = 0
        node.register_node_to_ring(
            node.id, 
            BOOTSTRAP_IP, 
            BOOTSTRAP_PORT, 
            node.wallet.public_key, 
            100 * NUMBER_OF_NODES)
        
        genesis_block = Block(0, 1)
        genesis_transaction = Transaction("0", node.wallet.public_key, 100 * NUMBER_OF_NODES, 100 * NUMBER_OF_NODES)
        genesis_block.transactions.append(genesis_transaction)
        node.wallet.transactions.append(genesis_transaction)
        genesis_block.current_hash = genesis_block.create_hash_object()
        node.chain.blocks.append(genesis_block)

        print("Bootstrap node registered to the ring")
    else:
        bootstrap_address = node.ip_port_to_address(BOOTSTRAP_IP, BOOTSTRAP_PORT)
        data = json.dumps({
            "ip": ip,
            "port": port,
            "public_key": node.wallet.public_key,
        })

        # use a thread to register the node to the ring
        def register_request():
            response = requests.post(
                bootstrap_address + "/register-node",
                data=data,
                headers=HEADERS)

            node.id = response.json()["id"]
            print(response.json()["message"])

        thread = threading.Thread(target=register_request)
        thread.start()

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
        public_key,
        0)
        
    if id == NUMBER_OF_NODES - 1:
        print("All nodes are registered to the ring")

        for ring_node in node.ring[1:]:
            node.share_ring(ring_node)
            node.share_chain(ring_node)

        for ring_node in node.ring[1:]:
            node.create_transaction(ring_node["public_key"], 100)

    print(f"Node with ID {id} registered to the ring")
    return jsonify({"message": f"Node with ID {id} registered to the ring", "id": id})

# node receives the ring from bootstrap node
@app.route('/receive-ring', methods=['POST'])
def receive_ring():
    node.ring = pickle.loads(request.get_data())

    print("Ring received from bootstrap node")
    return jsonify({"message": "Ring received from bootstrap node"})

# node receives the chain from bootstrap node
@app.route('/receive-chain', methods=['POST'])
def receive_chain():
    node.chain = pickle.loads(request.get_data())

    print("Chain received from bootstrap node")
    return jsonify({"message": "Chain received from bootstrap node"})

if __name__ == '__main__':
    app.run(host=ip, port=port)