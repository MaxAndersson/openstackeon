#!/bin/bash
#MASTER_IP=
export C_FORCE_ROOT="true"
export EON_CLIENT=$PWD/eonclient
celery -A app worker -b $MASTER_IP
