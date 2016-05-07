#!/bin/bash
#MASTER_IP=
export C_FORCE_ROOT="true"
sudo apt-get update
#sudo apt-get upgrade -y
sudo apt-get install -y python-pip gfortran git
sudo pip install celery
git clone https://github.com/MaxAndersson/openstackeon.git
base64 -d $PWD/openstackeon/eon/eon/openstackeon/eonclient.b64 > eonclient && chmod 777 eonclient
export EON_CLIENT =$PWD/eonclient
celery -A app worker -b $MASTER_IP --workdir=$PWD/openstackeon/eon/eon/oscelery
