#!/bin/sh

# Start the service application (app.py file) with arguments
python -u app.py --rabbit-host ${ADDRESS_RABBIT} --rabbit-user ${USERNAME_RABBIT} --rabbit-pass ${PASSWORD_RABBIT} --expected-address ${EXPECTED_ADDRESS} --replicas ${REPLICAS} --exchange-name ${EXCHANGE_NAME} --proxy-file ./proxy/proxy.txt
