import requests
import socket
import pickle
import os
import config
import subprocess

from PyInquirer import prompt
from PyInquirer import Validator, ValidationError
from argparse import ArgumentParser
from texttable import Texttable
from time import sleep

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

# Function that validates if the input is a number
class NumberValidator(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))

# Function for the home or exit option
def home_or_exit():
    home_or_exit_question = [{
            'type': 'list',
            'name': 'option',
            'message': 'select option:',
            'choices': ['home', 'exit']
        }]
    home_or_exit_answer = prompt(home_or_exit_question)['option']
    return home_or_exit_answer

# Main cli client function
def client():
    print("Loading...")
    sleep(1)
    while True:
        # Select what option to run
        question = [{
                'type': 'list',
                'name': 'method',
                'message': 'select option:',
                'choices': ['new transaction', 'view last transactions', 'balance', 'help', 'exit']
            }]
        answer = prompt(question)["method"]
        os.system('cls||clear')

        # Case of new transaction
        if answer == 'new transaction':
            print("new transaction")
            print("---------------")
            print()
            transaction_question = [{
                    'type': 'input',
                    'name': 'receiver',
                    'message': 'receiver\'s id:',
                    'validate': NumberValidator,
                    'filter': lambda val: int(val)
                },
                {
                    'type': 'input',
                    'name': 'amount',
                    'message': 'amount:',
                    'validate': NumberValidator,
                    'filter': lambda val: int(val)
                }]
            transaction_answer = prompt(transaction_question)
            confirmation_question = [{
                    'type': 'confirm',
                    'name': 'confirm',
                    'message': 'confirm the transaction ' + str(transaction_answer["amount"]) + ' -> ' + str(transaction_answer["receiver"]),
                    'default': False
                }]
            confirmation_answer = prompt(confirmation_question)["confirm"]

            # If transaction is confirmed, send it to the node
            if confirmation_answer:
                address = 'http://' + IPAddr + ':' + \
                    str(PORT) + '/api/create_transaction'
                try:
                    response = requests.post(address, data=transaction_answer).json()
                    message = response["message"]
                    print(message.lower() + '\n')
                except:
                    print("\nnode is not active, try again later\n")
                if home_or_exit() == 'exit':
                    break
                else:
                    os.system('cls||clear')
            else:
                print("\ntransaction aborted")

        # Case of view last transactions
        elif answer == 'view last transactions':
            print("transactions of last valid block of noobcash's blockchain")
            print("---------------------------------------------------------")
            print()
            address = 'http://' + IPAddr + ':' + str(PORT) + '/api/get_transactions'
            try:
                # Build a table with the transactions
                response = requests.get(address)
                data = pickle.loads(response._content)
                table = Texttable()
                table.set_deco(Texttable.HEADER | Texttable.VLINES)
                table.set_cols_dtype(['t', 't', 't', 't', 't'])
                table.set_cols_align(["c", "c", "c", "c", "c"])
                headers = ["sender_id", "receiver_id", "amount", "total", "change"]
                rows = []
                rows.append(headers)
                rows.extend(data)
                table.add_rows(rows)
                print(table.draw() + "\n")
            except:
                print("\nnode is not active, try again later\n")
            if home_or_exit() == 'exit':
                break
            else:
                os.system('cls||clear')

        # Case of show balance
        elif answer == 'balance':
            print("balance")
            print("-------")
            print()
            address = 'http://' + IPAddr + ':' + str(PORT) + '/api/get_balance'
            try:
                response = requests.get(address).json()
                balance = str(response['balance'])
                print('current balance: ' + balance + ' nbc\n')
            except:
                print("\nnode is not active, try again later\n")
            if home_or_exit() == 'exit':
                break
            else:
                os.system('cls||clear')

        # Case of help
        elif answer == 'help':
            print("help")
            print("----")
            print()
            print("options:")
            print("- new transaction: input the recipient id and the amount of nbc to send")
            print("- view last transactions: show the transactions of the last valid block")
            print("  of noobcash's blockchain")
            print("- balance: show current balance of your wallet")
            print("- help: you are here right now\n")

            if home_or_exit() == 'exit':
                break
            else:
                os.system('cls||clear')

        else:
            break


if __name__ == "__main__":
    # Define the argument parser
    parser = ArgumentParser(description='CLI client of noobcash.')
    required = parser.add_argument_group('required arguments')
    required.add_argument('-p', type=int, help='port to listen on', required=True)

    # Parse the given arguments
    args = parser.parse_args()
    PORT = args.p

    # Call the client function
    client()
