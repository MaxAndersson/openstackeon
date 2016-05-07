#!/bin/bash
sudo rabbitmq-server start
flower &> /dev/null &
