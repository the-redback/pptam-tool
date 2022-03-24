#!/bin/bash
set -euo pipefail
set -x

for i in $(docker stack services train-ticket --format "{{.Name}}")
do
   echo "Service ID: $i "
   docker service logs $i > ./logs/$i.log 2>&1
done
