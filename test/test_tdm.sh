#!/bin/bash -e

if [ $(echo ${PWD##*/}) != "test" ]
then 
  echo "Must run from test directory because I'm too lazy to fix all the paths"
  exit
fi
#cp ../etl/src/yang/__init__.py ../etl/src/yang/__init__.py.bak
# Replace the full list of YANG models with just a single one for repeatability (and brevity!)
cp __init__.py ../etl/src/yang/__init__.py
cd ..
# Permissions get setup oddly in the ETL process; clean up the directories before proceeding
# in case the workspace had a previous run already.
./clear_cache.sh
docker-compose -f docker-compose.yml build
# This might be needed, but sudo stuff is annoying.
#sudo sysctl -w vm.max_map_count=$(sudo sysctl -n vm.max_map_count)
docker-compose -f docker-compose.yml up -d
start=$SECONDS
echo "Measuring ETL runtime..."
while [[ $(docker ps --filter "name=tdm_etl.*" | grep -v CONTAINER) ]]
do
  sleep 60
done
duration=$(( SECONDS - start ))
hrs=$(( duration/3600 )); mins=$(( (duration-hrs*3600)/60)); secs=$(( duration-hrs*3600-mins*60 ))
printf 'Time spent: %02d:%02d:%02d\n' $hrs $mins $secs
