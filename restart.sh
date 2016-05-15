#! /usr/bin/env bash

sed -i 's/exec screen -c/exec screen -d -m -c/g' devstack/rejoin-stack.sh
cd devstack
./unstack.sh
./rejoin-stack.sh
sudo service apache2 restart
cd ..
screen -S stack -X screen -t keystone bash
screen -S stack -X stuff $'keystone-all\n'

