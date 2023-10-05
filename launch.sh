#!/bin/sh

# Start the service application (app.py file) with arguments
python -u app.py --rabbit-host ${RABBIT_HOST} --expected-address ${EXPECTED_ADDRESS} --replicas ${REPLICAS} --exchange-name ${EXCHANGE_NAME} --proxy-file ./proxy/proxy.txt --creds ./creds/creds
