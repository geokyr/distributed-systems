#!/bin/bash

keyfile=~/.ssh/id_rsa

for target in $(seq 1 5)
do
    scp -r -i $keyfile src/ user@snf-3529$target.ok-kno.grnetcloud.net:~
done
