# ntua-distributed-systems

Semester Project for the [**Distributed Systems**](https://www.ece.ntua.gr/en/undergraduate/courses/3377) course, during the 9th semester of the **School of Electrical and Computer Engineering at the National Technical University of Athens**.

## Team 1 - Members

- [**Kyriakopoulos Georgios**](https://github.com/geokyr)
- [**Tsertou Eleni**](https://github.com/EleniTser)
- [**Tzelepis Serafeim**](https://github.com/sertze)

## Project Description

The **Noobcash** project is a **Python-based** implementation of a **blockchain system** designed to **facilitate secure and decentralized transactions** without the need for a central authority. The system achieves this by utilizing a distributed database, which ensures that all nodes within the network have access to the same information and can verify the validity of any transaction.

As part of the project's development, several experiments were conducted to analyze the **system's performance** in terms of **throughput** and **block times** under varying conditions. These experiments involved testing different combinations of **block capacity** and **mining difficulty levels**. Additionally, the **scalability** of the system was tested by increasing the number of nodes within the network from 5 to 10. Through these experiments, valuable insights were gained into the system's behavior under different conditions, which can inform future improvements and developments in blockchain technology.

## Setup

Setup instructions are available on the project report. It mainly involves setting up a 5 node cluster, installing [Python3.8](https://www.python.org/downloads/release/python-380/), [pip](https://pypi.org/project/pip/) and the required dependencies or modules.

We used [~okeanos](https://astakos.okeanos-knossos.grnet.gr/ui/landing) to set up the cluster, which consists of 5 different virtual machines. Each one hosts either 1 or 2 nodes, depending on if we want to run the blockchain system with 5 or 10 nodes. The first node of the cluster is the bootstrap node, which is responsible for initializing the network and connecting the other nodes to it. The other nodes are responsible for mining blocks and verifying transactions, which is the case with the bootstrap node after the network has been initialized.

## SSH

We used SSH to connect to the nodes of the cluster. We also set up passwordless SSH, so that we can connect to the nodes without having to enter a password. To do this, we used the following 2 commands on a local machine to first generate a public/private key pair and then copy the public key to the remote nodes.
```
ssh-keygen
ssh-copy-id <user>@<remote-node>
```

Finally, we used the `remote-scp.sh` script, located under the `scripts/` directory, to copy any directory or file from a local machine to the remote nodes. This script is suited for the virtual machine names that the [~okeanos](https://astakos.okeanos-knossos.grnet.gr/ui/landing) service provides and needs the 5 digits that are in the first machine's name, copying the files to this and the next 4 machines (it supposes that the 5 machines have sequential digits on their names).

## Cluster

To update the hosts file, we used the `hosts.sh` script, located under the `scripts/` directory. This script updates the hosts file of each node with the IP addresses of the other nodes in the cluster, based on the local network we set up for the cluster (192.168.2.0/24), through the [~okeanos](https://astakos.okeanos-knossos.grnet.gr/ui/landing) service.

## Python

To download Python3.8 and pip, we used the `python-pip.sh` script, located under the `scripts/` directory, as well. This script downloads and builds Python3.8 from source and then downloads and installs pip.

To download and install the required dependencies, we used the `requirements.txt` file, located under the `src/` directory. This file contains all the required dependencies and their versions. To create the file we used the following commands, after installing all the necessary dependencies on the bootstrap machine:
```
cd src
pip freeze > requirements.txt
```

To install the dependencies on the rest of the machines, we used the following command, after having copied the file to them:
```
pip install -r requirements.txt
```

## Implementation

The blockchain system is implemented using Python3.8, with the help of the [Flask](https://flask.palletsprojects.com/en/2.2.x/) framework for the REST API and the [PyInquirer](https://pypi.org/project/PyInquirer/) module for the client. The blockchain system is using a REST API to handle calls between the nodes and a client in the form of a CLI (command-like interface) is also available, both under the `src/` directory. There is also a Python script that can be used to test the system with some sample transactions, under the `test/` directory, together with the directory containing the sample transactions.

An outline of the code structure is available on the project report. There, the different Python classes, instance variables and instance methods are listed and briefly explained. You can also find a short description of the REST API's endpoints and the client's available commands.

## Running the Project

### REST API

To see the blockchain system in action, every node needs to start its REST API on a port of choice. In the case of a network with 5 nodes, each machine will run the REST API on a single port, while in the case of 10 nodes, each machine will run it on two different ports. The REST API is started by running the `main.py` script, located under the `src/` directory, with the following command:
```
python3.8 main.py -p <port> -n <number-of-nodes> -c <capacity> -b
```

The `-p` flag is used to specify the port on which the REST API will run, while the `-n` flag is used to specify the number of nodes in the network. The `-c` flag is used to specify the block capacity, which is the maximum number of transactions that can be included in a block. The `-b` flag is optionally used to specify that the node is the bootstrap node, and should only be set on the bootstrap node (the first one on the network).

### CLI Client

After the REST API is running on every node, the client can be used to interact with the blockchain system. The client is started by running the `noobcash.py` file, located under the `src/` directory, with the following command:
```
python3.8 noobcash.py -p <port>
```

The `-p` flag is used to specify the port on which the REST API is listening on that node. The user can then select a command and enter the required arguments if needed to interact with the blockchain system.

### Testing

To test the blockchain system, we used the `run_test_files.py` script, located under the `test/` directory. This script sends 100 transactions to the blockchain system, coming from the node that the script is executed on. The script can be run with the following command:
```
python3.8 run_test_files.py -d <transactions-directory> -p <port>
```

The `-d` flag is used to specify the directory that contains the sample transactions (e.g. `transactions/5nodes`), while the `-p` flag is used to specify the port on which the REST API is listening on that node.

## Experiments

We ran some experiments on our blockchain, testing different combinations of block capacity and mining difficulty. These tests were conducted to measure the system's performance using two metrics, throughput and block times. We also tested the scalability of our system, by running the blockchain with 5 and 10 nodes in the network.

The results of these experiments, accompanied by some comparison graphs, our comments and a final conclusion are available on the project report.
