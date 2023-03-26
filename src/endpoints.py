import pickle
import node

from flask import Blueprint, jsonify, request

from node import Node, MINING_DIFFICULTY
from node import Node

# Define the node object of the current node and the number of nodes
node = Node()
n = 0

# Define a Blueprint for the api endpoints to use on the main.py file
rest_api = Blueprint('rest_api', __name__)


@rest_api.route('/register_node', methods=['POST'])
def register_node():
    '''Registers a new node in the network, called only by the bootstrap node'''

    # Get the arguments
    node_key = request.form.get('public_key')
    node_ip = request.form.get('ip')
    node_port = request.form.get('port')
    node_id = len(node.ring)

    # Add node in the list of registered nodes
    node.register_node_to_ring(
        id=node_id, ip=node_ip, port=node_port, public_key=node_key, balance=0)

    # When all nodes are registered, the bootstrap node sends them 
    # the chain, the ring and the first transaction
    if (node_id == n - 1):
        for ring_node in node.ring:
            if ring_node["id"] != node.id:
                node.share_chain(ring_node)
                node.share_ring(ring_node)
        for ring_node in node.ring:
            if ring_node["id"] != node.id:
                node.create_transaction(
                    ring_node['public_key'],
                    ring_node['id'],
                    100)

    return jsonify({'id': node_id})


@rest_api.route('/validate_transaction', methods=['POST'])
def validate_transaction():
    '''Validates an incoming transaction'''

    new_transaction = pickle.loads(request.get_data())
    if node.validate_transaction(new_transaction):
        return jsonify({'message': "OK"}), 200
    else:
        return jsonify({'message': "The signature is not valid"}), 401


@rest_api.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    '''Receives a transaction and add it to a block'''

    new_transaction = pickle.loads(request.get_data())
    node.add_transaction_to_block(new_transaction)

    return jsonify({'message': "OK"}), 200


@rest_api.route('/receive_block', methods=['POST'])
def receive_block():
    '''Receives a block, validate it and add it to the blockchain'''
    
    new_block = pickle.loads(request.get_data())
    node.chain_lock.acquire()
    if node.validate_block(new_block):
        # If the block is valid, add it to the blockchain, remove its
        # transactions from your unconfirmed_blocks and update previous hash and index 
        node.stop_mining = True
        with node.filter_lock:
            node.chain.blocks.append(new_block)
            node.chain_lock.release()
            node.filter_blocks(new_block)
            node.stop_mining = False
    else:
        # If the block is not valid, check either if the signature is not valid or
        # if you need to resolve conflicts
        if node.validate_previous_hash(new_block):
            node.chain_lock.release()
            return jsonify({'message': "The signature is not valid"}), 401
        else:
            # Resolve conflicts
            if node.resolve_conflicts(new_block):
                # Add block to the current blockchain
                node.stop_mining = True
                with node.filter_lock:
                    node.chain.blocks.append(new_block)
                    node.chain_lock.release()
                    # Remove the new_block's transactions from your unconfirmed_blocks
                    node.filter_blocks(new_block)
                    node.stop_mining = False
            else:
                node.chain_lock.release()
                return jsonify({'mesage': "Block rejected"}), 409

    return jsonify({'message': "OK"})


@rest_api.route('/receive_ring', methods=['POST'])
def receive_ring():
    '''Receives the ring from bootstrap'''
    
    node.ring = pickle.loads(request.get_data())
    # Update the id of the node based on the given ring
    for ring_node in node.ring:
        if ring_node['public_key'] == node.wallet.public_key:
            node.id = ring_node['id']
    return jsonify({'message': "OK"})


@rest_api.route('/receive_chain', methods=['POST'])
def receive_chain():
    '''Receives the blockchain'''

    node.chain = pickle.loads(request.get_data())
    return jsonify({'message': "OK"})


@rest_api.route('/send_chain', methods=['GET'])
def send_chain():
    '''Sends your chain to another node'''
    
    return pickle.dumps(node.chain)


@rest_api.route('/api/create_transaction', methods=['POST'])
def create_transaction():
    '''Creates a new transaction'''

    # Get the arguments
    receiver_id = int(request.form.get('receiver'))
    amount = int(request.form.get('amount'))

    # Find the receiver's address
    receiver_public_key = None
    for ring_node in node.ring:
        if (ring_node['id'] == receiver_id):
            receiver_public_key = ring_node['public_key']
    if (receiver_public_key and receiver_id != node.id):
        creation = node.create_transaction(receiver_public_key, receiver_id, amount)
        if creation["success"]:
            return jsonify({'message': 'Created the transaction', 'balance': node.wallet.wallet_balance(), "mining_time": creation["mining_time"]}), 200
        else:
            return jsonify({'message': 'Not enough coins', 'balance': node.wallet.wallet_balance(), "mining_time": creation["mining_time"]}), 400
    else:
        return jsonify({'message': 'Wrong receiver', "mining_time": 0}), 400


@rest_api.route('/api/get_balance', methods=['GET'])
def get_balance():
    '''Gets balance of the node'''
    
    return jsonify({'message': 'Current balance: ', 'balance': node.wallet.wallet_balance()})


@rest_api.route('/api/get_transactions', methods=['GET'])
def get_transactions():
    '''Gets transactions of the last confirmed block'''
    
    return pickle.dumps([tr.convert_to_list() for tr in node.chain.blocks[-1].transactions])


@rest_api.route('/api/get_id', methods=['GET'])
def get_id():
    '''Gets id of the node'''

    return jsonify({'message': node.id})


@rest_api.route('/api/get_metrics', methods=['GET'])
def get_metrics():
    '''Gets metrics of the network'''

    return jsonify({'num_blocks': len(node.chain.blocks), 'difficulty': MINING_DIFFICULTY, 'capacity': node.capacity})
