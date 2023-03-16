import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from argparse import ArgumentParser

import node

app = Flask(__name__)
CORS(app)

parser = ArgumentParser()
parser.add_argument('-h', '--host', default='127.0.0.1', type=str, help='host address')
parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
parser.add_argument('-b', '--is-bootstrap', default=False, type=bool, help='is this the bootstrap node?')
parser.add_argument('-n', '--number-of-nodes', default=0, type=int, help='number of children nodes')
args = parser.parse_args()
host = args.host
port = args.port
is_bootstrap = args.is_bootstrap
number_of_nodes = args.number_of_nodes

initial = node(host, port, is_bootstrap, number_of_nodes)

@app.route('/register-node', methods=['POST'])
def register_node():
    address = request.json['address']
    public_key = request.json['public_key']
    initial.register_node_to_ring(address, public_key)

    res = {"message": "Node registered"}
    return jsonify(res), 200

if __name__ == '__main__':
    app.run(host=host, port=port)
