#!/bin/sh

# Start the service application (app.py file) with arguments
python app.py --rabbit-host ${RABBIT_HOST} --expected-address ${EXPECTED_ADDRESS} --replicas ${REPLICAS} --exchange-name ${EXCHANGE_NAME}
