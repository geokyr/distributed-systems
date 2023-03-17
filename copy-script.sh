#!/bin/bash
for target in $(seq 1 5)
do
    scp -r src/ user@snf-3529$target.ok-kno.grnetcloud.net:~
done
