import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from argparse import ArgumentParser
from parameters import HEADERS, BOOTSTRAP_IP, BOOTSTRAP_PORT
from node import Node
import json

app = Flask(__name__)
CORS(app)

# global variables
node = Node()
number_of_nodes = 0

if __name__ == '__main__':

    # TODO: change -b and revamp the argument parser
    parser = ArgumentParser()
    parser.add_argument('-i', '--ip', default=BOOTSTRAP_IP, type=str, required=True, help='ip address')
    parser.add_argument('-p', '--port', default=5000, type=int, required=True, help='port to listen on')
    parser.add_argument('-b', '--is-bootstrap', default=False, type=bool, required=True, help='is this the bootstrap node?')
    parser.add_argument('-n', '--number-of-nodes', default=0, type=int, required=True, help='number of children nodes')

    args = parser.parse_args()
    ip = args.ip
    port = args.port
    is_bootstrap = args.is_bootstrap
    number_of_nodes = args.number_of_nodes

    if(is_bootstrap):
        node.id = 0
        node.register_node_to_ring(
            node.id, 
            BOOTSTRAP_IP, 
            BOOTSTRAP_PORT, 
            node.wallet.public_key, 
            100 * number_of_nodes)
        
        # TODO: unspent_coins add first transaction
        # TODO: genesis block
        print("Bootstrap node registered to the ring")
        app.run(host=ip, port=port)
    else:
        bootstrap_address = node.ip_port_to_address(BOOTSTRAP_IP, BOOTSTRAP_PORT)
        info = json.dumps({
            "ip": ip,
            "port": port,
            "public_key": node.wallet.public_key,
        })

        response = requests.post(
            bootstrap_address + "/register-node",
            data=info,
            headers=HEADERS)

        node.id = response.json()['id']
        print(f"Received {node.id} as a response from the bootstrap node")

        app.run(host=ip, port=port)

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

    # TODO: check if all nodes registered
    # def all_nodes_registered_to_ring(self):
    #     # all nodes are registered to the ring
    #     print("All nodes are registered to the ring")

    #     for node in self.ring[1:]:
    #         address = self.host_port_to_address(node)
    #         info = {"ring": self.ring, "chain": self.chain}
    #         json_info = json.dumps(info)

    #         requests.post(address + "/all-nodes-registered", data=json_info, headers=HEADERS)

    #     # wait for all nodes to receive the ring and chain
    #     time.sleep(2)

    return jsonify({"id": id})
