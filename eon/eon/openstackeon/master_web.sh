#!/bin/bash
sudo apt-get update -y
#sudo apt-get upgrade -y
echo "127.0.0.1       localhost EON EON.local" | sudo tee --append /etc/hosts > /dev/null
sudo apt-get install rabbitmq-server python-pip -y
sudo pip install flower
sudo rabbitmqctl add_user EON EON
sudo rabbitmqctl add_vhost EON
sudo rabbitmqctl set_permissions -p EON EON ".*" ".*" ".*"

#Web
echo "web" >> .env
sudo apt-get install -y python-numpy gfortran python-novaclient
sudo pip install novaclient ase flask

#Flower
flower &> /dev/null &
