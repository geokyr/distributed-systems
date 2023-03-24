import os
import requests
import socket
import pickle
import sys
import time
import subprocess

from argparse import ArgumentParser
from texttable import Texttable

# Add config file in our path.
sys.path.insert(0, '../src')
import config

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

# Get the IP address of the device
if config.LOCAL:
    IPAddr = '127.0.0.1'
else:
    hostname = socket.gethostname()
    IPAddr = ip_address()

total_time = 0
num_transactions = 0
total_mining_time = 0

def start_transactions():
    """This function sends the transactions of the text file"""

    global total_time
    global num_transactions
    global total_mining_time
    address = 'http://' + IPAddr + ':' + str(port) + '/api/create_transaction'
    with open(input_file, 'r') as f:
        for line in f:
            # Get the info of the transaction.
            line = line.split()
            receiver_id = int(line[0][2])
            amount = int(line[1])
            transaction = {'receiver': receiver_id, 'amount': amount}

            print(f'Transaction {id} -> {receiver_id} : {amount} nbc')

            # Send the current transaction.
            try:
                start_time = time.time()
                response = requests.post(address, data=transaction)
                end_time = time.time() - start_time
                message = response.json()["message"]
                mining_time = response.json()["mining_time"]
                if response.status_code == 200:
                    total_time += end_time
                    num_transactions += 1
                    total_mining_time += mining_time
                print(message + "\n")
            except:
                exit("Node is not active. Try again later.\n")

    print(f"\nTransactions for node {id} are done and the results are available on the results file")

    try:
        address = 'http://' + IPAddr + ':' + \
            str(port) + '/api/get_my_transactions'
        response = requests.get(address)
        data = pickle.loads(response._content)
    except:
        exit("\nSomething went wrong while receiving your transactions.\n")

    try:
        address = 'http://' + IPAddr + ':' + str(port) + '/api/get_metrics'
        response = requests.get(address).json()
        num_blocks = response['num_blocks'] - 1
        capacity = response['capacity']
        difficulty = response['difficulty']
        node_id = int(id)
        throughput = num_transactions/total_time
        block_time = total_mining_time/num_blocks

        with open('./results', 'a') as f: # +str(port)
            f.write('------------------------\n')
            f.write('Final results for node %d\n' %node_id)
            f.write('------------------------\n')
            f.write('Throughput: %f\n' %throughput)
            f.write('Block time %f\n' %block_time)
            f.write('Capacity: %d\n' %capacity)
            f.write('Difficulty: %d\n' %difficulty)
            f.write('\n')
    except:
        exit("\nSomething went wrong while receiving the total blocks.\n")

def get_id():
    address = 'http://' + IPAddr + ':' + str(port) + '/api/get_id'
    response = requests.get(address).json()
    message = response['message']
    return message


if __name__ == "__main__":
    # Define the argument parser.
    parser = ArgumentParser(description='Sends transactions in the noobcash blockchain given from a text file.')

    required = parser.add_argument_group('required arguments')
    required.add_argument('-d', help='Path to the directory of the transactions', required=True)
    required.add_argument('-p', type=int, help='Port that the api is listening on', required=True)

    # Parse the given arguments.
    args = parser.parse_args()
    input_dir = args.d
    port = args.p

    input("\nPress Enter to start the transactions\n")

    # Find the corresponding transaction file.
    id = get_id()
    input_file = os.path.join(input_dir, 'transactions' + str(id) + '.txt')

    start_transactions()
