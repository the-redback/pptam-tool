#!/bin/bash 
cd ./executed
for n in *; do printf './store.py ./executed/%s\n' "$n"; done > ../store_to_do.sh
chmod uog+x ../store_to_do.sh
