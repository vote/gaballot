#!/bin/bash

echo "Move downloaded file from ~/Downloads/?"
read confirm
[[ ${confirm:0:1} == y ]] && mv ~/Downloads/35211.zip .

make loaddata FILE=35211
echo "Please test in localhost."
echo ""
echo "Proceed with deployment to prod?"
read confirm
[[ ${confirm:0:1} != y ]] && exit

unset DATABASE_URL # this will cause load_data to read DB config from .env
# ASSUMPTION: .env has the prod db credentials
./db/load_data.sh 35211
