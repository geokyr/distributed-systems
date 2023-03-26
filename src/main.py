import time
import socket
import requests
import threading
import subprocess

import config
import endpoints

from flask_cors import CORS
from argparse import ArgumentParser
from flask import Flask

from transaction import Transaction
from endpoints import node, rest_api

# All nodes know the ip and the port of the bootstrap node
BOOTSTRAP_IP = config.BOOTSTRAP_IP
BOOTSTRAP_PORT = config.BOOTSTRAP_PORT

# Function that gets the ip address of the device.
def ip_address():
    # Run the ip command and capture its output
    result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)

    # Split the output into lines and iterate through them
    for line in result.stdout.split('\n'):
        # Check if the line contains an IPv4 address
        if 'inet ' in line and not '127.0.0.1' in line:
            # Extract the IPv4 address from the line
            ip_address = line.split()[1].split('/')[0]
            if ip_address.startswith('192.168'):
                return ip_address

    # Return None if no IPv4 address was found
    return None

# Get the IP address of the device.
if config.LOCAL:
    IPAddr = BOOTSTRAP_IP
else:
    hostname = socket.gethostname()
    IPAddr = ip_address()

# Register the blueprint with the endpoints
app = Flask(__name__)
app.register_blueprint(rest_api)
CORS(app)

if __name__ == '__main__':
    parser = ArgumentParser(description='Rest api of noobcash.')

    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional_arguments')

    required.add_argument('-p', type=int, help='port to listen on', required=True)
    required.add_argument('-n', type=int, help='number of nodes in the blockchain', required=True)
    required.add_argument('-c', type=int, help='capacity of a block', required=True)
    optional.add_argument('-b', '--bootstrap', action='store_true', help='set if the current node is the bootstrap')
    
    args = parser.parse_args()
    port = args.p
    endpoints.n = args.n
    node.capacity = args.c
    is_bootstrap = args.bootstrap

    if (is_bootstrap):
        # Bootstrap node, registers itself, creates the genesis block, the first transaction and adds it in the genesis block
        node.id = 0
        node.register_node_to_ring(
            node.id, BOOTSTRAP_IP, BOOTSTRAP_PORT, node.wallet.public_key, 100 * endpoints.n)

        # Create genesis block
        gen_block = node.create_new_block()
        gen_block.nonce = 0

        # Adds the first transaction on the genesis block
        first_transaction = Transaction("0", '0', node.wallet.public_key, node.id, 100 * endpoints.n, 100 * endpoints.n, None)
        gen_block.transactions.append(first_transaction)
        gen_block.hash = gen_block.hash_block()
        node.wallet.transactions.append(first_transaction)

        # Add genesis block in the blockchain
        node.chain.blocks.append(gen_block)
        node.current_block = None

        app.run(host=BOOTSTRAP_IP, port=BOOTSTRAP_PORT)
    else:
        # Other nodes, request to be registered on the ring
        register_address = 'http://' + BOOTSTRAP_IP + \
            ':' + BOOTSTRAP_PORT + '/register_node'

        def thread_function():
            time.sleep(2)

            data = {
                'public_key': node.wallet.public_key,
                'ip': IPAddr, 'port': port}

            response = requests.post(
                register_address,
                data=data)

            if response.status_code == 200:
                print("Node initialized")

            node.id = response.json()['id']

        req = threading.Thread(target=thread_function, args=())
        req.start()

        app.run(host=IPAddr, port=port)
