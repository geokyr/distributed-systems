#!/bin/bash

if [ $# -ne 1 ]
then
    echo "Usage: $0 <first_machine_number>"
    exit 1
fi

keyfile=~/.ssh/id_rsa
first_machine=$1

for target in $(seq $first_machine $((first_machine+4)))
do
    scp -r -i $keyfile ~/ntua-distributed-systems/src user@snf-$target.ok-kno.grnetcloud.net:~
    scp -i $keyfile ~/ntua-distributed-systems/test/run_test_files.py user@snf-$target.ok-kno.grnetcloud.net:~/test
done
