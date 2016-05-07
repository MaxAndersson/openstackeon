#!/bin/bash
#MASTER_IP=
export C_FORCE_ROOT="true"
sudo apt-get update
#sudo apt-get upgrade -y
sudo apt-get install -y python-pip gfortran
sudo pip install celery
#curl {source to app.py}  > app.py
#curl {source to eonclient.b64 (client base 64 encoded)} | base64 -d > eonclient && chmod 777 eonclient
export EON_CLIENT =$PWD/eonclient
celery -A app worker -b $MASTER_IP
