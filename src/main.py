import requests
import pickle
from flask import Flask, jsonify, request
from flask_cors import CORS
from argparse import ArgumentParser
from parameters import HEADERS, BOOTSTRAP_IP, BOOTSTRAP_PORT, NUMBER_OF_NODES
from node import Node
from transaction import Transaction
import json
import threading

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
        node.id = 0
        node.register_node_to_ring(
            node.id, 
            BOOTSTRAP_IP, 
            BOOTSTRAP_PORT, 
            node.wallet.public_key, 
            100 * NUMBER_OF_NODES)
        
        node.create_new_block()
        genesis_block = node.current_block
        genesis_transaction = Transaction("0", node.wallet.public_key, 100 * NUMBER_OF_NODES, 100 * NUMBER_OF_NODES, [])
        genesis_block.transactions.append(genesis_transaction)
        node.wallet.transactions.append(genesis_transaction)
        genesis_block.current_hash = genesis_block.create_hash()
        node.chain.blocks.append(genesis_block)
        node.current_block = None

        node.wait_for_all_nodes_to_register = threading.Event()
        thread = threading.Thread(target=node.all_nodes_registered)
        thread.start()
        
        print("Bootstrap node registered to the ring")
    else:
        bootstrap_address = node.ip_port_to_address(BOOTSTRAP_IP, BOOTSTRAP_PORT)
        data = json.dumps({
            "ip": ip,
            "port": port,
            "public_key": node.wallet.public_key,
        })

        response = requests.post(
            bootstrap_address + "/register-node",
            data=data,
            headers=HEADERS)

        node.id = response.json()["id"]
        print(response.json()["message"])

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

    if len(node.ring) == NUMBER_OF_NODES:
        node.wait_for_all_nodes_to_register.set()

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

# node sends its chain
@app.route('/send-chain', methods=['GET'])
def send_chain():
    return pickle.dumps(node.chain)

# node validates a transaction
@app.route('/validate-transaction', methods=['POST'])
def validate_transaction():
    transaction = pickle.loads(request.get_data())
    
    if node.validate_transaction(transaction):
        return jsonify({"message": "Transaction is valid"}), 200
    else:
        return jsonify({'message': "Cannot verify signature of transaction"}), 400

# node validates a block
@app.route('/validate-block', methods=['POST'])
def validate_block():
    block = pickle.loads(request.get_data())
    
    node.chain_lock.acquire()
    if node.validate_block(block):
        print("Block is valid")
        node.chain.blocks.append(block)
        node.chain_lock.release()
    else:
        if node.validate_previous_hash(block):
            print("Block previous hash is valid")
            node.chain_lock.release()
            return jsonify({"message": "Cannot verify signature of block"}), 400
        else:
            if node.resolve_conflicts(block):
                print("There was a conflict")
                node.chain.blocks.append(block)
                node.chain_lock.release()
            else:
                print("Failed to resolve conflict")
                node.chain_lock.release()
                return jsonify({"mesage": "Cannot accept block"}), 400
    print("Finally accepted block")
    return jsonify({"message": "Received block"}), 200

if __name__ == '__main__':
    app.run(host=ip, port=port)
